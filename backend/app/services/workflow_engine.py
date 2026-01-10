"""
Workflow Automation Engine

Intelligent dunning sequences and escalation management.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.invoice import Invoice, InvoiceStatus, AgingBucket
from ..models.customer import Customer, RiskLevel
from ..models.communication import Communication, CommunicationType, CommunicationChannel
from .ai_communication import ai_communication


class WorkflowRule:
    """Base class for workflow rules"""

    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority

    async def should_trigger(self, invoice: Invoice, customer: Customer) -> bool:
        """Check if rule should trigger"""
        raise NotImplementedError

    async def execute(self, invoice: Invoice, customer: Customer, db: AsyncSession) -> Dict[str, Any]:
        """Execute the rule"""
        raise NotImplementedError


class StandardReminderRule(WorkflowRule):
    """Standard reminder based on aging"""

    def __init__(self):
        super().__init__("standard_reminder", priority=1)

    async def should_trigger(self, invoice: Invoice, customer: Customer) -> bool:
        """Trigger reminders based on aging and last contact"""

        # Don't send if disputed
        if invoice.is_disputed:
            return False

        # Don't send if customer communications are disabled
        if not customer.communication_enabled or not customer.auto_reminders_enabled:
            return False

        # Calculate days since last reminder
        if invoice.last_reminder_sent:
            days_since_reminder = (datetime.now() - invoice.last_reminder_sent).days
        else:
            days_since_reminder = 999  # Never sent

        # Reminder schedule based on aging
        if invoice.aging_bucket == AgingBucket.CURRENT:
            return False  # Don't remind for current invoices

        elif invoice.aging_bucket == AgingBucket.DAYS_0_30:
            # Remind every 7 days
            return days_since_reminder >= 7

        elif invoice.aging_bucket == AgingBucket.DAYS_31_60:
            # Remind every 3 days
            return days_since_reminder >= 3

        elif invoice.aging_bucket == AgingBucket.DAYS_61_90:
            # Remind daily
            return days_since_reminder >= 1

        elif invoice.aging_bucket == AgingBucket.DAYS_90_PLUS:
            # Remind daily (escalation should also trigger)
            return days_since_reminder >= 1

        return False

    async def execute(self, invoice: Invoice, customer: Customer, db: AsyncSession) -> Dict[str, Any]:
        """Send reminder communication"""

        # Determine channel based on preferences and urgency
        if invoice.aging_bucket == AgingBucket.DAYS_90_PLUS:
            channels = [CommunicationChannel.EMAIL, CommunicationChannel.SMS]
        elif invoice.aging_bucket == AgingBucket.DAYS_61_90:
            channels = [CommunicationChannel.EMAIL, CommunicationChannel.SMS]
        else:
            channels = [CommunicationChannel.EMAIL]

        communications = []

        for channel in channels:
            # Generate message using AI
            message = await ai_communication.generate_collection_message(
                customer=customer,
                invoice=invoice,
                channel=channel.value,
                communication_type="reminder"
            )

            # Create communication record
            comm = Communication(
                customer_id=customer.id,
                invoice_id=invoice.id,
                channel=channel,
                communication_type=CommunicationType.REMINDER,
                subject=message.get("subject"),
                message_body=message.get("body"),
                recipient_email=customer.email if channel == CommunicationChannel.EMAIL else None,
                recipient_phone=customer.mobile or customer.phone if channel == CommunicationChannel.SMS else None,
                recipient_name=customer.contact_name,
                ai_generated=True,
                ai_model_used="gpt-4-turbo-preview",
                is_automated=True,
            )

            db.add(comm)
            communications.append(comm)

        # Update invoice
        invoice.last_reminder_sent = datetime.now()
        invoice.reminder_count += 1

        await db.commit()

        return {
            "rule": self.name,
            "action": "reminder_sent",
            "channels": [c.value for c in channels],
            "communication_ids": [c.id for c in communications],
        }


class EscalationRule(WorkflowRule):
    """Escalate severely overdue invoices"""

    def __init__(self):
        super().__init__("escalation", priority=2)

    async def should_trigger(self, invoice: Invoice, customer: Customer) -> bool:
        """Trigger escalation for 90+ days"""

        return (
            invoice.aging_bucket == AgingBucket.DAYS_90_PLUS
            and invoice.escalation_level < 2
            and not invoice.is_disputed
        )

    async def execute(self, invoice: Invoice, customer: Customer, db: AsyncSession) -> Dict[str, Any]:
        """Escalate invoice"""

        # Generate escalation message
        message = await ai_communication.generate_collection_message(
            customer=customer,
            invoice=invoice,
            channel="email",
            communication_type="escalation"
        )

        # Create communication
        comm = Communication(
            customer_id=customer.id,
            invoice_id=invoice.id,
            channel=CommunicationChannel.EMAIL,
            communication_type=CommunicationType.ESCALATION,
            subject=message.get("subject"),
            message_body=message.get("body"),
            recipient_email=customer.email,
            recipient_name=customer.contact_name,
            ai_generated=True,
            is_automated=True,
        )

        db.add(comm)

        # Update escalation level
        invoice.escalation_level += 1

        # Update customer risk level
        if customer.risk_level != RiskLevel.CRITICAL:
            customer.risk_level = RiskLevel.HIGH

        await db.commit()

        return {
            "rule": self.name,
            "action": "escalated",
            "new_escalation_level": invoice.escalation_level,
            "communication_id": comm.id,
        }


class PaymentPlanOfferRule(WorkflowRule):
    """Offer payment plan for large amounts"""

    def __init__(self):
        super().__init__("payment_plan_offer", priority=1)

    async def should_trigger(self, invoice: Invoice, customer: Customer) -> bool:
        """Offer payment plan for large invoices 30+ days overdue"""

        return (
            invoice.amount_outstanding >= 10000
            and invoice.aging_bucket in [AgingBucket.DAYS_31_60, AgingBucket.DAYS_61_90]
            and invoice.reminder_count >= 2
            and not invoice.is_disputed
        )

    async def execute(self, invoice: Invoice, customer: Customer, db: AsyncSession) -> Dict[str, Any]:
        """Send payment plan offer"""

        # Generate payment plan offer message
        message = await ai_communication.generate_collection_message(
            customer=customer,
            invoice=invoice,
            channel="email",
            communication_type="payment_plan_offer"
        )

        # Create communication
        comm = Communication(
            customer_id=customer.id,
            invoice_id=invoice.id,
            channel=CommunicationChannel.EMAIL,
            communication_type=CommunicationType.PAYMENT_PLAN_OFFER,
            subject=message.get("subject"),
            message_body=message.get("body"),
            recipient_email=customer.email,
            recipient_name=customer.contact_name,
            ai_generated=True,
            is_automated=True,
        )

        db.add(comm)
        await db.commit()

        return {
            "rule": self.name,
            "action": "payment_plan_offered",
            "communication_id": comm.id,
        }


class WorkflowEngine:
    """Main workflow automation engine"""

    def __init__(self):
        self.rules: List[WorkflowRule] = [
            StandardReminderRule(),
            EscalationRule(),
            PaymentPlanOfferRule(),
        ]
        # Sort rules by priority
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    async def process_invoice(
        self,
        invoice: Invoice,
        customer: Customer,
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        Process an invoice through all applicable workflow rules

        Args:
            invoice: Invoice to process
            customer: Related customer
            db: Database session

        Returns:
            List of actions taken
        """

        actions = []

        for rule in self.rules:
            if await rule.should_trigger(invoice, customer):
                try:
                    result = await rule.execute(invoice, customer, db)
                    actions.append(result)
                except Exception as e:
                    print(f"Rule {rule.name} failed: {e}")
                    continue

        return actions

    async def process_all_invoices(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Process all open invoices through workflow rules

        Returns:
            Summary of actions taken
        """

        # Get all open invoices
        result = await db.execute(
            select(Invoice)
            .where(Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE]))
            .where(Invoice.amount_outstanding > 0)
        )
        invoices = result.scalars().all()

        total_processed = 0
        total_actions = 0
        actions_by_type = {}

        for invoice in invoices:
            # Get customer
            customer_result = await db.execute(
                select(Customer).where(Customer.id == invoice.customer_id)
            )
            customer = customer_result.scalar_one_or_none()

            if not customer:
                continue

            # Process invoice
            actions = await self.process_invoice(invoice, customer, db)

            total_processed += 1
            total_actions += len(actions)

            for action in actions:
                action_type = action.get("action", "unknown")
                actions_by_type[action_type] = actions_by_type.get(action_type, 0) + 1

        return {
            "total_invoices_processed": total_processed,
            "total_actions_taken": total_actions,
            "actions_by_type": actions_by_type,
        }


# Singleton instance
workflow_engine = WorkflowEngine()

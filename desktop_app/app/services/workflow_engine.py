"""
Workflow Engine

Automated workflow execution for sending payment reminders and collection notices.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Automated workflow execution engine"""

    def __init__(self, db_manager, email_client=None, sms_client=None):
        self.db_manager = db_manager
        self.email_client = email_client
        self.sms_client = sms_client

    def run_workflows(self, session: Session) -> Dict:
        """
        Run all automated workflows

        Args:
            session: Database session

        Returns:
            Dictionary with execution stats
        """
        stats = {
            'reminders_sent': 0,
            'collection_notices_sent': 0,
            'thank_you_sent': 0,
            'errors': 0,
        }

        try:
            # 1. Send payment reminders for overdue invoices
            stats['reminders_sent'] = self._send_payment_reminders(session)

            # 2. Send collection notices for severely overdue
            stats['collection_notices_sent'] = self._send_collection_notices(session)

            # 3. Send thank you messages for recent payments
            stats['thank_you_sent'] = self._send_thank_you_messages(session)

            logger.info(f"Workflow execution complete: {stats}")

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            stats['errors'] += 1

        return stats

    def _send_payment_reminders(self, session: Session) -> int:
        """Send payment reminders for overdue invoices"""
        from ..models.database import Invoice, Customer, InvoiceStatus, CommunicationLog

        # Find invoices that are 7-30 days overdue and haven't been reminded recently
        overdue_invoices = session.query(Invoice).join(Customer).filter(
            Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE]),
            Invoice.days_outstanding >= 7,
            Invoice.days_outstanding < 90
        ).all()

        sent_count = 0

        for invoice in overdue_invoices:
            # Check if we've already sent a reminder recently (within 7 days)
            recent_reminder = session.query(CommunicationLog).filter(
                CommunicationLog.invoice_id == invoice.id,
                CommunicationLog.communication_type == 'reminder',
                CommunicationLog.sent_at >= datetime.now() - timedelta(days=7)
            ).first()

            if recent_reminder:
                continue

            # Send reminder
            success = self._send_email_reminder(invoice, session)
            if success:
                sent_count += 1

        return sent_count

    def _send_collection_notices(self, session: Session) -> int:
        """Send collection notices for severely overdue invoices"""
        from ..models.database import Invoice, Customer, InvoiceStatus, CommunicationLog

        # Find invoices that are 90+ days overdue
        severely_overdue = session.query(Invoice).join(Customer).filter(
            Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE]),
            Invoice.days_outstanding >= 90
        ).all()

        sent_count = 0

        for invoice in severely_overdue:
            # Check if we've sent a collection notice recently (within 14 days)
            recent_notice = session.query(CommunicationLog).filter(
                CommunicationLog.invoice_id == invoice.id,
                CommunicationLog.communication_type == 'collection_notice',
                CommunicationLog.sent_at >= datetime.now() - timedelta(days=14)
            ).first()

            if recent_notice:
                continue

            # Send collection notice
            success = self._send_collection_notice(invoice, session)
            if success:
                sent_count += 1

        return sent_count

    def _send_thank_you_messages(self, session: Session) -> int:
        """Send thank you messages for recent payments"""
        from ..models.database import Invoice, Customer, InvoiceStatus, CommunicationLog

        # Find recently paid invoices (last 3 days)
        recent_payments = session.query(Invoice).join(Customer).filter(
            Invoice.status == InvoiceStatus.PAID,
            Invoice.updated_at >= datetime.now() - timedelta(days=3)
        ).all()

        sent_count = 0

        for invoice in recent_payments:
            # Check if we've already sent thank you
            existing_thank_you = session.query(CommunicationLog).filter(
                CommunicationLog.invoice_id == invoice.id,
                CommunicationLog.communication_type == 'thank_you'
            ).first()

            if existing_thank_you:
                continue

            # Send thank you
            success = self._send_thank_you(invoice, session)
            if success:
                sent_count += 1

        return sent_count

    def _send_email_reminder(self, invoice, session: Session) -> bool:
        """Send email reminder for an invoice"""
        from ..models.database import CommunicationLog

        try:
            customer = invoice.customer

            # Generate email content
            subject = f"Payment Reminder - Invoice {invoice.invoice_number}"

            message = f"""Dear {customer.company_name},

This is a friendly reminder that Invoice {invoice.invoice_number} is now {invoice.days_outstanding} days overdue.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Original Amount: ${invoice.original_amount:,.2f}
- Amount Outstanding: ${invoice.amount_outstanding:,.2f}
- Due Date: {invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'N/A'}
- Days Overdue: {invoice.days_outstanding}

Please arrange payment at your earliest convenience. If you have any questions or concerns, please don't hesitate to contact us.

Thank you for your prompt attention to this matter.

Best regards,
Collections Team
"""

            # Send email (if email client configured)
            if self.email_client and customer.email:
                self.email_client.send_email(
                    to=customer.email,
                    subject=subject,
                    body=message
                )
                status = 'sent'
                error_msg = None
            else:
                # Log as pending if no email client
                status = 'pending'
                error_msg = "Email client not configured" if not self.email_client else "No email address"

            # Log communication
            log = CommunicationLog(
                customer_id=customer.id,
                invoice_id=invoice.id,
                communication_type='reminder',
                channel='email',
                sent_at=datetime.now(),
                status=status,
                message_content=message,
                error_message=error_msg
            )
            session.add(log)
            session.commit()

            logger.info(f"Sent payment reminder for invoice {invoice.invoice_number} to {customer.company_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send payment reminder: {e}")

            # Log failed communication
            log = CommunicationLog(
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                communication_type='reminder',
                channel='email',
                sent_at=datetime.now(),
                status='failed',
                error_message=str(e)
            )
            session.add(log)
            session.commit()

            return False

    def _send_collection_notice(self, invoice, session: Session) -> bool:
        """Send collection notice for severely overdue invoice"""
        from ..models.database import CommunicationLog

        try:
            customer = invoice.customer

            # Generate more urgent message
            subject = f"URGENT: Collection Notice - Invoice {invoice.invoice_number}"

            message = f"""Dear {customer.company_name},

URGENT PAYMENT REQUIRED

This is a formal collection notice for Invoice {invoice.invoice_number}, which is now {invoice.days_outstanding} days past due.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Amount Outstanding: ${invoice.amount_outstanding:,.2f}
- Original Due Date: {invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'N/A'}
- Days Overdue: {invoice.days_outstanding}

IMMEDIATE ACTION REQUIRED:
Payment must be received within 7 business days to avoid further collection action.

If payment has already been sent, please provide proof of payment immediately.

For payment arrangements or to discuss this matter, please contact us as soon as possible.

Collections Department
"""

            # Send email
            if self.email_client and customer.email:
                self.email_client.send_email(
                    to=customer.email,
                    subject=subject,
                    body=message
                )
                status = 'sent'
                error_msg = None
            else:
                status = 'pending'
                error_msg = "Email client not configured" if not self.email_client else "No email address"

            # Log communication
            log = CommunicationLog(
                customer_id=customer.id,
                invoice_id=invoice.id,
                communication_type='collection_notice',
                channel='email',
                sent_at=datetime.now(),
                status=status,
                message_content=message,
                error_message=error_msg
            )
            session.add(log)
            session.commit()

            logger.info(f"Sent collection notice for invoice {invoice.invoice_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send collection notice: {e}")

            log = CommunicationLog(
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                communication_type='collection_notice',
                channel='email',
                sent_at=datetime.now(),
                status='failed',
                error_message=str(e)
            )
            session.add(log)
            session.commit()

            return False

    def _send_thank_you(self, invoice, session: Session) -> bool:
        """Send thank you message for payment"""
        from ..models.database import CommunicationLog

        try:
            customer = invoice.customer

            subject = f"Thank You - Payment Received for Invoice {invoice.invoice_number}"

            message = f"""Dear {customer.company_name},

Thank you for your recent payment on Invoice {invoice.invoice_number}.

We have successfully received your payment and your account has been updated.

Invoice Details:
- Invoice Number: {invoice.invoice_number}
- Amount Paid: ${invoice.original_amount:,.2f}
- Payment Date: {datetime.now().strftime('%Y-%m-%d')}

We appreciate your business and prompt payment!

If you have any questions, please don't hesitate to contact us.

Best regards,
Accounting Team
"""

            # Send email
            if self.email_client and customer.email:
                self.email_client.send_email(
                    to=customer.email,
                    subject=subject,
                    body=message
                )
                status = 'sent'
                error_msg = None
            else:
                status = 'pending'
                error_msg = "Email client not configured" if not self.email_client else "No email address"

            # Log communication
            log = CommunicationLog(
                customer_id=customer.id,
                invoice_id=invoice.id,
                communication_type='thank_you',
                channel='email',
                sent_at=datetime.now(),
                status=status,
                message_content=message,
                error_message=error_msg
            )
            session.add(log)
            session.commit()

            logger.info(f"Sent thank you message for invoice {invoice.invoice_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send thank you message: {e}")

            log = CommunicationLog(
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                communication_type='thank_you',
                channel='email',
                sent_at=datetime.now(),
                status='failed',
                error_message=str(e)
            )
            session.add(log)
            session.commit()

            return False


# Singleton instance
workflow_engine = None


def get_workflow_engine(db_manager):
    """Get or create workflow engine instance"""
    global workflow_engine
    if workflow_engine is None:
        workflow_engine = WorkflowEngine(db_manager)
    return workflow_engine

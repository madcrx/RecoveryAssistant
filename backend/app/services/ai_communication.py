"""
AI-Powered Communication Engine

Generates personalized, context-aware collection messages using OpenAI GPT-4.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
from openai import AsyncOpenAI

from ..core.config import settings
from ..models.customer import Customer, RiskLevel
from ..models.invoice import Invoice, AgingBucket


class CommunicationEngine:
    """AI-powered communication generator for collections"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def generate_collection_message(
        self,
        customer: Customer,
        invoice: Invoice,
        channel: str = "email",
        communication_type: str = "reminder"
    ) -> Dict[str, str]:
        """
        Generate personalized collection message

        Args:
            customer: Customer object with history
            invoice: Invoice object
            channel: Communication channel (email, sms)
            communication_type: Type of message (reminder, escalation, etc.)

        Returns:
            Dict with subject and body
        """

        # Build context for AI
        context = self._build_context(customer, invoice)

        # Get tone based on aging and relationship
        tone = self._determine_tone(customer, invoice)

        # Generate message using OpenAI
        if channel == "email":
            return await self._generate_email(context, tone, communication_type)
        elif channel == "sms":
            return await self._generate_sms(context, tone, communication_type)
        else:
            return await self._generate_email(context, tone, communication_type)

    def _build_context(self, customer: Customer, invoice: Invoice) -> Dict[str, Any]:
        """Build comprehensive context for AI message generation"""

        days_overdue = (datetime.now().date() - invoice.due_date).days

        return {
            "customer_name": customer.company_name,
            "contact_name": customer.contact_name or "valued customer",
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date.strftime("%B %d, %Y"),
            "due_date": invoice.due_date.strftime("%B %d, %Y"),
            "amount": f"${invoice.amount_outstanding:,.2f}",
            "days_overdue": days_overdue,
            "aging_bucket": invoice.aging_bucket.value,
            "total_outstanding": f"${customer.current_balance:,.2f}",
            "payment_score": customer.payment_score,
            "average_days_to_pay": customer.average_days_to_pay or 30,
            "reminder_count": invoice.reminder_count,
            "risk_level": customer.risk_level.value,
            "has_payment_promise": invoice.payment_promise_date is not None,
            "payment_promise_date": invoice.payment_promise_date.strftime("%B %d, %Y") if invoice.payment_promise_date else None,
        }

    def _determine_tone(self, customer: Customer, invoice: Invoice) -> str:
        """Determine appropriate tone based on customer relationship and invoice aging"""

        # Excellent payment history → friendly
        if customer.payment_score > 90 and invoice.aging_bucket in [AgingBucket.CURRENT, AgingBucket.DAYS_0_30]:
            return "friendly_reminder"

        # Good customer, slightly overdue → professional
        elif customer.payment_score > 75 and invoice.aging_bucket == AgingBucket.DAYS_31_60:
            return "professional"

        # Moderate issues → firm
        elif invoice.aging_bucket == AgingBucket.DAYS_61_90:
            return "firm"

        # Serious delinquency → urgent
        elif invoice.aging_bucket == AgingBucket.DAYS_90_PLUS:
            return "urgent"

        # High risk customer → cautious_firm
        elif customer.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return "firm"

        # Default
        return "professional"

    async def _generate_email(
        self,
        context: Dict[str, Any],
        tone: str,
        communication_type: str
    ) -> Dict[str, str]:
        """Generate email subject and body"""

        tone_descriptions = {
            "friendly_reminder": "friendly and appreciative, acknowledging the good payment relationship",
            "professional": "professional and courteous, focusing on resolution",
            "firm": "firm but respectful, emphasizing urgency and consequences",
            "urgent": "urgent and serious, indicating final notice and legal implications",
        }

        system_prompt = f"""You are an expert collections specialist writing {tone_descriptions.get(tone, 'professional')} collection emails.

Your goal is to:
1. Encourage prompt payment while maintaining customer relationships
2. Make it extremely easy for the customer to pay (include clear payment instructions)
3. Prevent disputes by being clear and specific about the invoice details
4. Show empathy and offer solutions (payment plans if needed)
5. NEVER be aggressive, threatening, or rude
6. Keep the message concise and actionable

Tone: {tone}
Communication Type: {communication_type}

IMPORTANT:
- Always include a clear call-to-action with payment link placeholder: [PAYMENT_LINK]
- For amounts over $10,000 or aging 60+ days, mention payment plan options
- For 90+ days, mention escalation consequences professionally
- Always maintain professionalism and compliance with debt collection laws
"""

        user_prompt = f"""Generate a collection email with the following details:

Customer: {context['customer_name']}
Contact: {context['contact_name']}
Invoice: {context['invoice_number']}
Invoice Date: {context['invoice_date']}
Due Date: {context['due_date']}
Amount: {context['amount']}
Days Overdue: {context['days_overdue']}
Aging Bucket: {context['aging_bucket']}
Total Outstanding: {context['total_outstanding']}
Previous Reminders: {context['reminder_count']}
Payment Score: {context['payment_score']}/100
Average Days to Pay: {context['average_days_to_pay']}

Generate:
1. A compelling subject line (max 60 characters)
2. A professional email body (max 250 words)

Format as JSON:
{{
    "subject": "subject line here",
    "body": "email body here"
}}
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            return {
                "subject": result.get("subject", f"Payment Reminder: Invoice {context['invoice_number']}"),
                "body": result.get("body", "")
            }

        except Exception as e:
            print(f"AI email generation failed: {e}")
            return self._fallback_email(context)

    async def _generate_sms(
        self,
        context: Dict[str, Any],
        tone: str,
        communication_type: str
    ) -> Dict[str, str]:
        """Generate SMS message (160 characters max)"""

        system_prompt = """You are generating concise SMS collection messages (max 160 characters).

Requirements:
- Be professional and clear
- Include invoice number and amount
- Include payment link placeholder: [LINK]
- Stay under 160 characters
- No aggressive language
"""

        user_prompt = f"""Generate SMS for:
Invoice: {context['invoice_number']}
Amount: {context['amount']}
Days Overdue: {context['days_overdue']}
Company: {context['customer_name']}
Tone: {tone}

Return JSON: {{"body": "sms text here"}}
"""

        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=100,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            return {
                "subject": "",
                "body": result.get("body", self._fallback_sms(context))
            }

        except Exception as e:
            print(f"AI SMS generation failed: {e}")
            return {"subject": "", "body": self._fallback_sms(context)}

    def _fallback_email(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Fallback email template if AI fails"""
        subject = f"Payment Reminder: Invoice {context['invoice_number']}"

        body = f"""Dear {context['contact_name']},

This is a friendly reminder that invoice {context['invoice_number']} for {context['amount']} is currently past due.

Invoice Details:
- Invoice Number: {context['invoice_number']}
- Invoice Date: {context['invoice_date']}
- Due Date: {context['due_date']}
- Amount Due: {context['amount']}
- Days Overdue: {context['days_overdue']}

Please make a payment at your earliest convenience by clicking the link below:
[PAYMENT_LINK]

If you have already sent payment or have any questions about this invoice, please contact us immediately.

Thank you for your prompt attention to this matter.

Best regards,
Accounts Receivable Team
"""

        return {"subject": subject, "body": body}

    def _fallback_sms(self, context: Dict[str, Any]) -> str:
        """Fallback SMS template if AI fails"""
        return f"Payment reminder: Invoice {context['invoice_number']} for {context['amount']} is past due. Pay now: [LINK]"


# Singleton instance
ai_communication = CommunicationEngine()

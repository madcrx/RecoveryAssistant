"""
Payment Processing Service

Handles payment processing through Stripe with multiple payment methods.
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date
import stripe

from ..core.config import settings
from ..models.payment import PaymentMethod, PaymentStatus


class PaymentProcessor:
    """Stripe-based payment processing"""

    def __init__(self):
        stripe.api_key = settings.STRIPE_API_KEY

    async def create_payment_link(
        self,
        invoice_id: int,
        customer_email: str,
        customer_name: str,
        amount: float,
        invoice_number: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a secure payment link for customer

        Args:
            invoice_id: Internal invoice ID
            customer_email: Customer email
            customer_name: Customer name
            amount: Amount to charge
            invoice_number: Invoice reference number
            description: Optional payment description

        Returns:
            Dict with payment_url and payment_intent_id
        """

        try:
            # Create or retrieve Stripe customer
            stripe_customer = await self._get_or_create_customer(
                email=customer_email,
                name=customer_name
            )

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                customer=stripe_customer.id,
                metadata={
                    "invoice_id": str(invoice_id),
                    "invoice_number": invoice_number,
                },
                description=description or f"Payment for Invoice {invoice_number}",
                automatic_payment_methods={"enabled": True},
            )

            # Create checkout session for easier payment
            checkout_session = stripe.checkout.Session.create(
                customer=stripe_customer.id,
                payment_intent=payment_intent.id,
                mode="payment",
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(amount * 100),
                        "product_data": {
                            "name": f"Invoice {invoice_number}",
                            "description": description or "Invoice Payment",
                        },
                    },
                    "quantity": 1,
                }],
                success_url=f"{settings.CORS_ORIGINS[0]}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.CORS_ORIGINS[0]}/payment/cancel",
                metadata={
                    "invoice_id": str(invoice_id),
                    "invoice_number": invoice_number,
                }
            )

            return {
                "payment_url": checkout_session.url,
                "payment_intent_id": payment_intent.id,
                "session_id": checkout_session.id,
                "customer_id": stripe_customer.id,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    async def create_payment_plan(
        self,
        invoice_id: int,
        customer_email: str,
        customer_name: str,
        total_amount: float,
        num_installments: int,
        invoice_number: str
    ) -> Dict[str, Any]:
        """
        Create a payment plan with multiple installments

        Args:
            invoice_id: Internal invoice ID
            customer_email: Customer email
            customer_name: Customer name
            total_amount: Total amount to pay
            num_installments: Number of installments
            invoice_number: Invoice reference

        Returns:
            Dict with payment plan details
        """

        installment_amount = total_amount / num_installments

        try:
            # Create Stripe customer
            stripe_customer = await self._get_or_create_customer(
                email=customer_email,
                name=customer_name
            )

            # Create subscription for installments
            price = stripe.Price.create(
                unit_amount=int(installment_amount * 100),
                currency="usd",
                recurring={"interval": "month"},
                product_data={
                    "name": f"Payment Plan: Invoice {invoice_number}",
                },
                metadata={
                    "invoice_id": str(invoice_id),
                    "installment_amount": str(installment_amount),
                    "total_installments": str(num_installments),
                }
            )

            subscription = stripe.Subscription.create(
                customer=stripe_customer.id,
                items=[{"price": price.id}],
                metadata={
                    "invoice_id": str(invoice_id),
                    "invoice_number": invoice_number,
                    "total_amount": str(total_amount),
                    "num_installments": str(num_installments),
                },
                # Cancel after specified number of payments
                cancel_at_period_end=False,
            )

            return {
                "subscription_id": subscription.id,
                "installment_amount": installment_amount,
                "num_installments": num_installments,
                "total_amount": total_amount,
                "status": "active",
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    async def process_ach_payment(
        self,
        customer_id: int,
        amount: float,
        bank_account_token: str,
        invoice_number: str
    ) -> Dict[str, Any]:
        """
        Process ACH/bank transfer payment

        Args:
            customer_id: Stripe customer ID
            amount: Amount to charge
            bank_account_token: Bank account token from Stripe.js
            invoice_number: Invoice reference

        Returns:
            Dict with payment details
        """

        try:
            # Create ACH payment
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency="usd",
                customer=customer_id,
                payment_method=bank_account_token,
                payment_method_types=["us_bank_account"],
                metadata={"invoice_number": invoice_number},
                confirm=True,
            )

            return {
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": amount,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    async def verify_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Verify payment status

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            Dict with payment verification details
        """

        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "status": payment_intent.status,
                "amount": payment_intent.amount / 100,
                "paid": payment_intent.status == "succeeded",
                "invoice_id": payment_intent.metadata.get("invoice_id"),
                "invoice_number": payment_intent.metadata.get("invoice_number"),
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    async def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[float] = None,
        reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """
        Refund a payment

        Args:
            payment_intent_id: Stripe payment intent ID
            amount: Optional partial refund amount
            reason: Refund reason

        Returns:
            Dict with refund details
        """

        try:
            refund_params = {
                "payment_intent": payment_intent_id,
                "reason": reason,
            }

            if amount:
                refund_params["amount"] = int(amount * 100)

            refund = stripe.Refund.create(**refund_params)

            return {
                "refund_id": refund.id,
                "status": refund.status,
                "amount": refund.amount / 100,
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")

    async def _get_or_create_customer(
        self,
        email: str,
        name: str
    ) -> Any:
        """Get existing Stripe customer or create new one"""

        # Search for existing customer
        customers = stripe.Customer.list(email=email, limit=1)

        if customers.data:
            return customers.data[0]

        # Create new customer
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata={"source": "recovery_assistant"}
        )

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Handle Stripe webhook events

        Args:
            payload: Raw request payload
            signature: Stripe signature header

        Returns:
            Dict with event details
        """

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )

            # Handle different event types
            if event.type == "payment_intent.succeeded":
                payment_intent = event.data.object
                return {
                    "event_type": "payment_succeeded",
                    "payment_intent_id": payment_intent.id,
                    "amount": payment_intent.amount / 100,
                    "invoice_id": payment_intent.metadata.get("invoice_id"),
                }

            elif event.type == "payment_intent.payment_failed":
                payment_intent = event.data.object
                return {
                    "event_type": "payment_failed",
                    "payment_intent_id": payment_intent.id,
                    "error": payment_intent.last_payment_error.message if payment_intent.last_payment_error else None,
                }

            elif event.type == "charge.refunded":
                charge = event.data.object
                return {
                    "event_type": "charge_refunded",
                    "charge_id": charge.id,
                    "amount_refunded": charge.amount_refunded / 100,
                }

            return {"event_type": event.type}

        except ValueError as e:
            raise Exception(f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            raise Exception(f"Invalid signature: {str(e)}")


# Singleton instance
payment_processor = PaymentProcessor()

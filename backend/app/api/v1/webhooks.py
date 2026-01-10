"""
Webhooks API Endpoints

Handle external service webhooks (Stripe, SendGrid, Twilio).
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...core.database import get_db
from ...models.invoice import Invoice, InvoiceStatus
from ...models.payment import Payment, PaymentStatus, PaymentMethod
from ...services.payment_processor import payment_processor

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    db: AsyncSession = Depends(get_db)
):
    """Handle Stripe webhook events"""

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    payload = await request.body()

    try:
        # Verify and process webhook
        event_data = await payment_processor.handle_webhook(payload, stripe_signature)

        # Handle payment success
        if event_data.get("event_type") == "payment_succeeded":
            payment_intent_id = event_data.get("payment_intent_id")
            amount = event_data.get("amount")
            invoice_id = event_data.get("invoice_id")

            if invoice_id:
                # Get invoice
                result = await db.execute(
                    select(Invoice).where(Invoice.id == int(invoice_id))
                )
                invoice = result.scalar_one_or_none()

                if invoice:
                    # Create payment record
                    import datetime

                    payment = Payment(
                        payment_reference=f"PAY-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                        customer_id=invoice.customer_id,
                        invoice_id=invoice.id,
                        amount=amount,
                        payment_method=PaymentMethod.CREDIT_CARD,
                        payment_date=datetime.date.today(),
                        status=PaymentStatus.COMPLETED,
                        stripe_payment_intent_id=payment_intent_id,
                        is_reconciled=False,
                    )

                    db.add(payment)

                    # Update invoice
                    invoice.amount_paid += amount
                    invoice.amount_outstanding = max(0, invoice.original_amount - invoice.amount_paid)

                    if invoice.amount_outstanding == 0:
                        invoice.status = InvoiceStatus.PAID
                        invoice.paid_date = datetime.date.today()
                    elif invoice.amount_paid > 0:
                        invoice.status = InvoiceStatus.PARTIALLY_PAID

                    await db.commit()

        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sendgrid")
async def sendgrid_webhook(request: Request):
    """Handle SendGrid email events (opens, clicks, bounces)"""

    events = await request.json()

    # Process SendGrid events
    # TODO: Update communication records with delivery status

    return {"success": True}


@router.post("/twilio")
async def twilio_webhook(request: Request):
    """Handle Twilio SMS events"""

    data = await request.form()

    # Process Twilio events
    # TODO: Update communication records with SMS status

    return {"success": True}

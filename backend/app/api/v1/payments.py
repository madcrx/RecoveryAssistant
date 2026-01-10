"""
Payments API Endpoints

Handle payment processing and payment links.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ...core.database import get_db
from ...models.invoice import Invoice
from ...models.customer import Customer
from ...models.payment import Payment, PaymentMethod, PaymentStatus
from ...services.payment_processor import payment_processor

router = APIRouter()


class PaymentLinkRequest(BaseModel):
    invoice_id: int


class PaymentPlanRequest(BaseModel):
    invoice_id: int
    num_installments: int = 3


@router.post("/create-link")
async def create_payment_link(
    request: PaymentLinkRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a secure payment link for an invoice"""

    # Get invoice
    result = await db.execute(
        select(Invoice).where(Invoice.id == request.invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get customer
    result = await db.execute(
        select(Customer).where(Customer.id == invoice.customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Create payment link
    try:
        payment_link_data = await payment_processor.create_payment_link(
            invoice_id=invoice.id,
            customer_email=customer.email or "noreply@example.com",
            customer_name=customer.company_name,
            amount=invoice.amount_outstanding,
            invoice_number=invoice.invoice_number,
            description=f"Payment for Invoice {invoice.invoice_number}"
        )

        return {
            "success": True,
            "payment_url": payment_link_data["payment_url"],
            "invoice_number": invoice.invoice_number,
            "amount": invoice.amount_outstanding,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-payment-plan")
async def create_payment_plan(
    request: PaymentPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a payment plan for an invoice"""

    # Get invoice
    result = await db.execute(
        select(Invoice).where(Invoice.id == request.invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get customer
    result = await db.execute(
        select(Customer).where(Customer.id == invoice.customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Create payment plan
    try:
        payment_plan_data = await payment_processor.create_payment_plan(
            invoice_id=invoice.id,
            customer_email=customer.email or "noreply@example.com",
            customer_name=customer.company_name,
            total_amount=invoice.amount_outstanding,
            num_installments=request.num_installments,
            invoice_number=invoice.invoice_number
        )

        return {
            "success": True,
            **payment_plan_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_payments(
    customer_id: Optional[int] = None,
    invoice_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List payments with optional filters"""

    query = select(Payment)

    if customer_id:
        query = query.where(Payment.customer_id == customer_id)

    if invoice_id:
        query = query.where(Payment.invoice_id == invoice_id)

    if status:
        query = query.where(Payment.status == status)

    query = query.limit(limit).offset(offset).order_by(Payment.payment_date.desc())

    result = await db.execute(query)
    payments = result.scalars().all()

    return {
        "payments": [
            {
                "id": p.id,
                "payment_reference": p.payment_reference,
                "customer_id": p.customer_id,
                "invoice_id": p.invoice_id,
                "amount": p.amount,
                "payment_method": p.payment_method.value,
                "payment_date": p.payment_date.isoformat(),
                "status": p.status.value,
            }
            for p in payments
        ],
        "total": len(payments),
    }

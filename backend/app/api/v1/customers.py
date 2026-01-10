"""
Customers API Endpoints

Manage customer information and history.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from ...core.database import get_db
from ...models.customer import Customer, RiskLevel

router = APIRouter()


class CustomerCreate(BaseModel):
    customer_number: str
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None


class CustomerUpdate(BaseModel):
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    communication_enabled: Optional[bool] = None
    auto_reminders_enabled: Optional[bool] = None
    preferred_contact_method: Optional[str] = None


@router.get("/")
async def list_customers(
    risk_level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all customers with optional filters"""

    query = select(Customer).where(Customer.is_active == True)

    if risk_level:
        query = query.where(Customer.risk_level == risk_level)

    query = query.limit(limit).offset(offset).order_by(Customer.company_name)

    result = await db.execute(query)
    customers = result.scalars().all()

    return {
        "customers": [
            {
                "id": c.id,
                "customer_number": c.customer_number,
                "company_name": c.company_name,
                "contact_name": c.contact_name,
                "email": c.email,
                "phone": c.phone,
                "current_balance": c.current_balance,
                "risk_level": c.risk_level.value,
                "payment_score": c.payment_score,
            }
            for c in customers
        ],
        "total": len(customers),
    }


@router.get("/{customer_id}")
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get customer details with full history"""

    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {
        "id": customer.id,
        "customer_number": customer.customer_number,
        "company_name": customer.company_name,
        "contact_name": customer.contact_name,
        "email": customer.email,
        "phone": customer.phone,
        "mobile": customer.mobile,
        "address": {
            "line1": customer.address_line1,
            "line2": customer.address_line2,
            "city": customer.city,
            "state": customer.state,
            "postal_code": customer.postal_code,
            "country": customer.country,
        },
        "financial": {
            "credit_limit": customer.credit_limit,
            "current_balance": customer.current_balance,
            "total_invoiced": customer.total_invoiced,
            "total_paid": customer.total_paid,
        },
        "metrics": {
            "risk_level": customer.risk_level.value,
            "payment_score": customer.payment_score,
            "average_days_to_pay": customer.average_days_to_pay,
        },
        "preferences": {
            "preferred_contact_method": customer.preferred_contact_method,
            "timezone": customer.timezone,
            "communication_enabled": customer.communication_enabled,
            "auto_reminders_enabled": customer.auto_reminders_enabled,
        },
        "notes": customer.notes,
    }


@router.post("/")
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new customer"""

    # Check if customer number already exists
    result = await db.execute(
        select(Customer).where(Customer.customer_number == customer_data.customer_number)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Customer number already exists")

    customer = Customer(**customer_data.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return {
        "id": customer.id,
        "customer_number": customer.customer_number,
        "company_name": customer.company_name,
    }


@router.patch("/{customer_id}")
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update customer information"""

    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Update fields
    update_data = customer_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    await db.commit()

    return {
        "success": True,
        "message": "Customer updated successfully"
    }

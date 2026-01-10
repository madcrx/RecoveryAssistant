"""
Analytics API Endpoints

Provide collection metrics and insights.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from ...core.database import get_db
from ...models.invoice import Invoice, InvoiceStatus, AgingBucket
from ...models.customer import Customer
from ...models.payment import Payment, PaymentStatus

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db)
):
    """Get key collection metrics for dashboard"""

    # Total outstanding
    result = await db.execute(
        select(func.sum(Invoice.amount_outstanding))
        .where(Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE]))
    )
    total_outstanding = result.scalar() or 0

    # Count by aging bucket
    aging_counts = {}
    aging_amounts = {}

    for bucket in AgingBucket:
        count_result = await db.execute(
            select(func.count(Invoice.id))
            .where(Invoice.aging_bucket == bucket)
            .where(Invoice.amount_outstanding > 0)
        )
        aging_counts[bucket.value] = count_result.scalar() or 0

        amount_result = await db.execute(
            select(func.sum(Invoice.amount_outstanding))
            .where(Invoice.aging_bucket == bucket)
        )
        aging_amounts[bucket.value] = amount_result.scalar() or 0

    # Payments this month
    first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(func.sum(Payment.amount))
        .where(Payment.status == PaymentStatus.COMPLETED)
        .where(Payment.payment_date >= first_of_month.date())
    )
    payments_this_month = result.scalar() or 0

    # Average days to pay
    result = await db.execute(
        select(func.avg(Customer.average_days_to_pay))
        .where(Customer.average_days_to_pay.isnot(None))
    )
    avg_days_to_pay = result.scalar() or 0

    # Collection rate (payments / invoices in last 30 days)
    thirty_days_ago = datetime.now().date() - timedelta(days=30)

    result = await db.execute(
        select(func.sum(Invoice.original_amount))
        .where(Invoice.invoice_date >= thirty_days_ago)
    )
    invoiced_last_30 = result.scalar() or 0

    result = await db.execute(
        select(func.sum(Payment.amount))
        .where(Payment.payment_date >= thirty_days_ago)
        .where(Payment.status == PaymentStatus.COMPLETED)
    )
    collected_last_30 = result.scalar() or 0

    collection_rate = (collected_last_30 / invoiced_last_30 * 100) if invoiced_last_30 > 0 else 0

    # High risk customers count
    result = await db.execute(
        select(func.count(Customer.id))
        .where(Customer.risk_level.in_(['high', 'critical']))
    )
    high_risk_count = result.scalar() or 0

    return {
        "total_outstanding": total_outstanding,
        "aging_distribution": {
            "counts": aging_counts,
            "amounts": aging_amounts,
        },
        "payments_this_month": payments_this_month,
        "average_days_to_pay": round(avg_days_to_pay, 1),
        "collection_rate_30_days": round(collection_rate, 2),
        "high_risk_customers": high_risk_count,
        "metrics": {
            "dso": round(avg_days_to_pay, 1),  # Days Sales Outstanding
            "cei": round(collection_rate, 2),  # Collection Effectiveness Index
        }
    }


@router.get("/trends")
async def get_collection_trends(
    days: int = 90,
    db: AsyncSession = Depends(get_db)
):
    """Get collection trends over time"""

    start_date = datetime.now().date() - timedelta(days=days)

    # Get daily payment totals
    result = await db.execute(
        select(
            Payment.payment_date,
            func.sum(Payment.amount).label('total')
        )
        .where(Payment.payment_date >= start_date)
        .where(Payment.status == PaymentStatus.COMPLETED)
        .group_by(Payment.payment_date)
        .order_by(Payment.payment_date)
    )

    daily_payments = [
        {
            "date": row.payment_date.isoformat(),
            "amount": row.total
        }
        for row in result
    ]

    return {
        "period_days": days,
        "daily_payments": daily_payments,
    }

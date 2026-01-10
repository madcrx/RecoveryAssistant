"""
Receivables API Endpoints

Upload and manage aged receivables reports.
"""

from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ...core.database import get_db
from ...models.customer import Customer
from ...models.invoice import Invoice, InvoiceStatus, AgingBucket
from ...services.pdf_parser import pdf_parser
from ...services.workflow_engine import workflow_engine

router = APIRouter()


@router.post("/upload")
async def upload_receivables_report(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process an aged receivables PDF report

    This endpoint:
    1. Parses the PDF to extract invoice data
    2. Creates or updates customer and invoice records
    3. Triggers automated collection workflows
    """

    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Read file content
    content = await file.read()

    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    try:
        # Parse PDF
        data = await pdf_parser.parse_pdf(content, file.filename)

        if not data.invoices:
            raise HTTPException(
                status_code=400,
                detail="No invoice data could be extracted from the PDF"
            )

        # Process extracted data
        invoices_created = 0
        invoices_updated = 0
        customers_created = 0

        for invoice_data in data.invoices:
            # Get or create customer
            customer_name = invoice_data.get('customer_name', '').strip()
            if not customer_name:
                continue

            result = await db.execute(
                select(Customer).where(Customer.company_name == customer_name)
            )
            customer = result.scalar_one_or_none()

            if not customer:
                # Create new customer
                customer = Customer(
                    customer_number=f"CUST-{datetime.now().strftime('%Y%m%d')}-{customers_created + 1:04d}",
                    company_name=customer_name,
                    communication_enabled=True,
                    auto_reminders_enabled=True,
                )
                db.add(customer)
                await db.flush()
                customers_created += 1

            # Get or create invoice
            invoice_number = invoice_data.get('invoice_number', '').strip()
            if not invoice_number:
                continue

            result = await db.execute(
                select(Invoice).where(Invoice.invoice_number == invoice_number)
            )
            invoice = result.scalar_one_or_none()

            amount = invoice_data.get('amount', 0) or 0
            invoice_date = invoice_data.get('invoice_date')
            days_outstanding = invoice_data.get('days_outstanding', 0)

            # Determine aging bucket
            if days_outstanding <= 0:
                aging_bucket = AgingBucket.CURRENT
            elif days_outstanding <= 30:
                aging_bucket = AgingBucket.DAYS_0_30
            elif days_outstanding <= 60:
                aging_bucket = AgingBucket.DAYS_31_60
            elif days_outstanding <= 90:
                aging_bucket = AgingBucket.DAYS_61_90
            else:
                aging_bucket = AgingBucket.DAYS_90_PLUS

            if not invoice:
                # Create new invoice
                import datetime as dt

                invoice = Invoice(
                    invoice_number=invoice_number,
                    customer_id=customer.id,
                    invoice_date=invoice_date or dt.date.today(),
                    due_date=invoice_data.get('due_date') or dt.date.today(),
                    original_amount=amount,
                    amount_outstanding=amount,
                    status=InvoiceStatus.OPEN if amount > 0 else InvoiceStatus.PAID,
                    aging_bucket=aging_bucket,
                    days_outstanding=days_outstanding,
                )
                db.add(invoice)
                invoices_created += 1
            else:
                # Update existing invoice
                invoice.amount_outstanding = amount
                invoice.aging_bucket = aging_bucket
                invoice.days_outstanding = days_outstanding
                invoice.status = InvoiceStatus.OPEN if amount > 0 else InvoiceStatus.PAID
                invoices_updated += 1

        await db.commit()

        # Trigger workflows in background
        if background_tasks:
            background_tasks.add_task(workflow_engine.process_all_invoices, db)

        return {
            "success": True,
            "filename": file.filename,
            "report_date": data.report_date.isoformat() if data.report_date else None,
            "total_outstanding": data.total_outstanding,
            "aging_summary": data.aging_summary,
            "statistics": {
                "invoices_created": invoices_created,
                "invoices_updated": invoices_updated,
                "customers_created": customers_created,
                "total_invoices": len(data.invoices),
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@router.get("/")
async def list_invoices(
    status: Optional[str] = None,
    aging_bucket: Optional[str] = None,
    customer_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List invoices with optional filters"""

    query = select(Invoice)

    if status:
        query = query.where(Invoice.status == status)

    if aging_bucket:
        query = query.where(Invoice.aging_bucket == aging_bucket)

    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)

    query = query.limit(limit).offset(offset).order_by(Invoice.due_date.desc())

    result = await db.execute(query)
    invoices = result.scalars().all()

    return {
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "customer_id": inv.customer_id,
                "invoice_date": inv.invoice_date.isoformat(),
                "due_date": inv.due_date.isoformat(),
                "amount_outstanding": inv.amount_outstanding,
                "status": inv.status.value,
                "aging_bucket": inv.aging_bucket.value,
                "days_outstanding": inv.days_outstanding,
            }
            for inv in invoices
        ],
        "total": len(invoices),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get invoice details"""

    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "customer_id": invoice.customer_id,
        "invoice_date": invoice.invoice_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "original_amount": invoice.original_amount,
        "amount_paid": invoice.amount_paid,
        "amount_outstanding": invoice.amount_outstanding,
        "status": invoice.status.value,
        "aging_bucket": invoice.aging_bucket.value,
        "days_outstanding": invoice.days_outstanding,
        "reminder_count": invoice.reminder_count,
        "last_reminder_sent": invoice.last_reminder_sent.isoformat() if invoice.last_reminder_sent else None,
        "is_disputed": invoice.is_disputed,
    }


@router.post("/trigger-workflows")
async def trigger_workflows(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger workflow processing for all invoices"""

    background_tasks.add_task(workflow_engine.process_all_invoices, db)

    return {
        "success": True,
        "message": "Workflow processing triggered in background"
    }

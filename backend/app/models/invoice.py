from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import String, Float, Integer, DateTime, Boolean, Date, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class InvoiceStatus(str, enum.Enum):
    OPEN = "open"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"
    WRITTEN_OFF = "written_off"


class AgingBucket(str, enum.Enum):
    CURRENT = "current"  # Not yet due
    DAYS_0_30 = "0-30"
    DAYS_31_60 = "31-60"
    DAYS_61_90 = "61-90"
    DAYS_90_PLUS = "90+"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Invoice Information
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True
    )

    # Dates
    invoice_date: Mapped[date] = mapped_column(Date, index=True)
    due_date: Mapped[date] = mapped_column(Date, index=True)
    paid_date: Mapped[Optional[date]] = mapped_column(Date)

    # Financial
    original_amount: Mapped[float] = mapped_column(Float)
    amount_paid: Mapped[float] = mapped_column(Float, default=0.0)
    amount_outstanding: Mapped[float] = mapped_column(Float)

    # Status & Aging
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus),
        default=InvoiceStatus.OPEN,
        index=True
    )
    aging_bucket: Mapped[AgingBucket] = mapped_column(
        Enum(AgingBucket),
        default=AgingBucket.CURRENT,
        index=True
    )
    days_outstanding: Mapped[int] = mapped_column(Integer, default=0)

    # Collection Tracking
    last_reminder_sent: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)
    payment_promise_date: Mapped[Optional[date]] = mapped_column(Date)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0)

    # AI/ML Predictions
    collection_probability: Mapped[Optional[float]] = mapped_column(Float)
    predicted_payment_date: Mapped[Optional[date]] = mapped_column(Date)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    po_number: Mapped[Optional[str]] = mapped_column(String(100))
    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="invoices")
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    communications: Mapped[List["Communication"]] = relationship(
        "Communication",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )
    disputes: Mapped[List["Dispute"]] = relationship(
        "Dispute",
        back_populates="invoice",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number}: ${self.amount_outstanding}>"

    @property
    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        return datetime.now().date() > self.due_date and self.amount_outstanding > 0

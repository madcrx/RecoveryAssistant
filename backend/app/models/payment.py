from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, Date, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class PaymentMethod(str, enum.Enum):
    ACH = "ach"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    WIRE = "wire"
    CHECK = "check"
    CASH = "cash"
    OTHER = "other"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Payment Information
    payment_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True
    )
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("invoices.id", ondelete="SET NULL"),
        index=True
    )

    # Financial
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    # Payment Details
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod))
    payment_date: Mapped[date] = mapped_column(Date, index=True)
    processed_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        index=True
    )

    # External References
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(String(255))
    external_reference: Mapped[Optional[str]] = mapped_column(String(255))

    # Payment Plan
    is_payment_plan: Mapped[bool] = mapped_column(Integer, default=False)
    payment_plan_id: Mapped[Optional[int]] = mapped_column(Integer)
    installment_number: Mapped[Optional[int]] = mapped_column(Integer)

    # Reconciliation
    is_reconciled: Mapped[bool] = mapped_column(Integer, default=False)
    reconciled_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reconciled_by: Mapped[Optional[int]] = mapped_column(Integer)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)

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
    customer: Mapped["Customer"] = relationship("Customer", back_populates="payments")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="payments")

    def __repr__(self) -> str:
        return f"<Payment {self.payment_reference}: ${self.amount}>"

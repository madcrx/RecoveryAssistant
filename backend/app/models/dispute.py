from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_INTERNAL = "pending_internal"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class DisputeReason(str, enum.Enum):
    INCORRECT_AMOUNT = "incorrect_amount"
    SERVICE_NOT_RECEIVED = "service_not_received"
    QUALITY_ISSUE = "quality_issue"
    DUPLICATE_INVOICE = "duplicate_invoice"
    CREDIT_NOT_APPLIED = "credit_not_applied"
    PRICING_DISCREPANCY = "pricing_discrepancy"
    ALREADY_PAID = "already_paid"
    OTHER = "other"


class Dispute(Base):
    __tablename__ = "disputes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Related Entities
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.id", ondelete="CASCADE"),
        index=True
    )
    invoice_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("invoices.id", ondelete="CASCADE"),
        index=True
    )

    # Dispute Information
    dispute_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[DisputeStatus] = mapped_column(
        Enum(DisputeStatus),
        default=DisputeStatus.OPEN,
        index=True
    )
    reason: Mapped[DisputeReason] = mapped_column(Enum(DisputeReason))

    # Financial Impact
    disputed_amount: Mapped[float] = mapped_column(Float)
    adjusted_amount: Mapped[Optional[float]] = mapped_column(Float)
    credit_issued: Mapped[float] = mapped_column(Float, default=0.0)

    # Details
    customer_description: Mapped[str] = mapped_column(Text)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Timeline
    reported_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    acknowledged_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    target_resolution_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Assignment
    assigned_to_user_id: Mapped[Optional[int]] = mapped_column(Integer)
    escalated_to_user_id: Mapped[Optional[int]] = mapped_column(Integer)

    # Supporting Evidence
    documents: Mapped[Optional[dict]] = mapped_column(JSON)
    evidence_urls: Mapped[Optional[dict]] = mapped_column(JSON)

    # Communication
    customer_contact_preference: Mapped[Optional[str]] = mapped_column(String(50))
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Resolution
    is_valid_dispute: Mapped[Optional[bool]] = mapped_column(Integer)
    resolution_type: Mapped[Optional[str]] = mapped_column(String(100))

    # AI Analysis
    ai_suggested_resolution: Mapped[Optional[str]] = mapped_column(Text)
    similar_disputes: Mapped[Optional[dict]] = mapped_column(JSON)

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
    customer: Mapped["Customer"] = relationship("Customer", back_populates="disputes")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="disputes")

    def __repr__(self) -> str:
        return f"<Dispute {self.dispute_number}: {self.status.value}>"

    @property
    def days_open(self) -> int:
        """Calculate how many days the dispute has been open"""
        if self.resolved_date:
            delta = self.resolved_date - self.reported_date
        else:
            delta = datetime.now(self.reported_date.tzinfo) - self.reported_date
        return delta.days

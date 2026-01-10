from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Float, Integer, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Basic Information
    customer_number: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255), index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    mobile: Mapped[Optional[str]] = mapped_column(String(50))

    # Address
    address_line1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(2), default="US")

    # Financial Information
    credit_limit: Mapped[float] = mapped_column(Float, default=0.0)
    current_balance: Mapped[float] = mapped_column(Float, default=0.0)
    total_invoiced: Mapped[float] = mapped_column(Float, default=0.0)
    total_paid: Mapped[float] = mapped_column(Float, default=0.0)

    # Risk & Scoring
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel),
        default=RiskLevel.LOW
    )
    payment_score: Mapped[float] = mapped_column(Float, default=100.0)
    average_days_to_pay: Mapped[Optional[float]] = mapped_column(Float)

    # Preferences
    preferred_contact_method: Mapped[str] = mapped_column(
        String(20),
        default="email"
    )
    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")
    communication_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    communications: Mapped[List["Communication"]] = relationship(
        "Communication",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    disputes: Mapped[List["Dispute"]] = relationship(
        "Dispute",
        back_populates="customer",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Customer {self.customer_number}: {self.company_name}>"

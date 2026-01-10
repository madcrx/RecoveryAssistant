from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    PORTAL = "portal"
    LETTER = "letter"


class CommunicationType(str, enum.Enum):
    REMINDER = "reminder"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    PAYMENT_PLAN_OFFER = "payment_plan_offer"
    ESCALATION = "escalation"
    DISPUTE_RESPONSE = "dispute_response"
    THANK_YOU = "thank_you"
    FINAL_NOTICE = "final_notice"


class CommunicationStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    RESPONDED = "responded"
    BOUNCED = "bounced"
    FAILED = "failed"


class Communication(Base):
    __tablename__ = "communications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Related Entities
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

    # Communication Details
    channel: Mapped[CommunicationChannel] = mapped_column(Enum(CommunicationChannel))
    communication_type: Mapped[CommunicationType] = mapped_column(Enum(CommunicationType))
    status: Mapped[CommunicationStatus] = mapped_column(
        Enum(CommunicationStatus),
        default=CommunicationStatus.QUEUED,
        index=True
    )

    # Content
    subject: Mapped[Optional[str]] = mapped_column(String(500))
    message_body: Mapped[str] = mapped_column(Text)
    template_used: Mapped[Optional[str]] = mapped_column(String(100))

    # Recipients
    recipient_email: Mapped[Optional[str]] = mapped_column(String(255))
    recipient_phone: Mapped[Optional[str]] = mapped_column(String(50))
    recipient_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Engagement Metrics
    open_count: Mapped[int] = mapped_column(Integer, default=0)
    click_count: Mapped[int] = mapped_column(Integer, default=0)

    # External References
    sendgrid_message_id: Mapped[Optional[str]] = mapped_column(String(255))
    twilio_message_sid: Mapped[Optional[str]] = mapped_column(String(255))

    # AI Generation
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100))
    personalization_data: Mapped[Optional[dict]] = mapped_column(JSON)

    # Response
    customer_response: Mapped[Optional[str]] = mapped_column(Text)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Integer)

    # Metadata
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_automated: Mapped[bool] = mapped_column(Boolean, default=True)
    sent_by_user_id: Mapped[Optional[int]] = mapped_column(Integer)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

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
    customer: Mapped["Customer"] = relationship("Customer", back_populates="communications")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="communications")

    def __repr__(self) -> str:
        return f"<Communication {self.channel.value}: {self.communication_type.value}>"

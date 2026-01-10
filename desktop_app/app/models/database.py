"""
Database Manager - SQLite Database

Handles local SQLite database for storing receivables data.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, date
import enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


# Enums
class AgingBucket(str, enum.Enum):
    CURRENT = "current"
    DAYS_0_30 = "0-30"
    DAYS_31_60 = "31-60"
    DAYS_61_90 = "61-90"
    DAYS_90_PLUS = "90+"


class InvoiceStatus(str, enum.Enum):
    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIALLY_PAID = "partially_paid"
    DISPUTED = "disputed"
    WRITTEN_OFF = "written_off"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommunicationChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    PORTAL = "portal"


# Models
class Customer(Base):
    """Customer/Debtor model"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    customer_id = Column(String(100), unique=True, index=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    mobile = Column(String(50))

    # Financial
    current_balance = Column(Float, default=0.0)
    credit_limit = Column(Float, default=0.0)

    # Scoring
    payment_score = Column(Integer, default=50)  # 0-100
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM)
    average_days_to_pay = Column(Integer)

    # Communication preferences
    communication_enabled = Column(Boolean, default=True)
    auto_reminders_enabled = Column(Boolean, default=True)
    preferred_channel = Column(SQLEnum(CommunicationChannel), default=CommunicationChannel.EMAIL)

    # Integration
    xero_contact_id = Column(String(100), unique=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Invoice(Base):
    """Invoice/Receivable model"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    customer_id = Column(Integer, nullable=False)

    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date)

    # Amounts
    original_amount = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    amount_outstanding = Column(Float, nullable=False)

    # Status
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.OPEN)
    aging_bucket = Column(SQLEnum(AgingBucket), default=AgingBucket.CURRENT)
    days_outstanding = Column(Integer, default=0)

    # Dispute
    is_disputed = Column(Boolean, default=False)
    dispute_reason = Column(Text)

    # Communication
    reminder_count = Column(Integer, default=0)
    last_reminder_sent = Column(DateTime)
    escalation_level = Column(Integer, default=0)

    # Payment promise
    payment_promise_date = Column(Date)
    payment_promise_amount = Column(Float)

    # Integration
    xero_invoice_id = Column(String(100), unique=True)

    # Reference
    reference = Column(String(255))
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Payment(Base):
    """Payment transaction model"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    payment_reference = Column(String(100), unique=True, index=True)
    customer_id = Column(Integer, nullable=False)
    invoice_id = Column(Integer)

    # Payment details
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String(50))  # credit_card, ach, wire, check, cash

    # Status
    status = Column(String(50))  # completed, pending, failed, refunded

    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_date = Column(DateTime)

    # Stripe
    stripe_payment_intent_id = Column(String(255))
    stripe_charge_id = Column(String(255))

    # Integration
    xero_payment_id = Column(String(100))

    # Reference
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Communication(Base):
    """Communication log model"""
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    invoice_id = Column(Integer)

    # Communication details
    channel = Column(SQLEnum(CommunicationChannel), nullable=False)
    communication_type = Column(String(50))  # reminder, escalation, payment_confirmation, etc.
    subject = Column(String(500))
    message_body = Column(Text)

    # Recipients
    recipient_email = Column(String(255))
    recipient_phone = Column(String(50))
    recipient_name = Column(String(255))

    # Status
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    status = Column(String(50))  # queued, sent, delivered, failed, bounced

    # AI
    ai_generated = Column(Boolean, default=False)
    ai_model_used = Column(String(100))

    # Automation
    is_automated = Column(Boolean, default=False)
    workflow_id = Column(Integer)

    # Response
    response_received = Column(Boolean, default=False)
    response_date = Column(DateTime)
    response_text = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)


class WorkflowLog(Base):
    """Workflow execution log"""
    __tablename__ = "workflow_logs"

    id = Column(Integer, primary_key=True)
    workflow_name = Column(String(100))
    invoice_id = Column(Integer)
    customer_id = Column(Integer)

    # Execution
    executed_at = Column(DateTime, default=datetime.now)
    status = Column(String(50))  # success, failed, skipped
    action_taken = Column(String(255))
    result = Column(Text)

    # Details
    rule_triggered = Column(String(100))
    notes = Column(Text)


class SyncLog(Base):
    """Integration sync log"""
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    integration = Column(String(50))  # xero, quickbooks, etc.
    sync_type = Column(String(50))  # invoices, contacts, payments

    # Execution
    started_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    status = Column(String(50))  # running, completed, failed

    # Results
    records_synced = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    errors = Column(Text)

    # Details
    notes = Column(Text)


class DatabaseManager:
    """Manages SQLite database connection and operations"""

    def __init__(self, db_path: str = None):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """

        if not db_path:
            # Default to user's Documents folder
            documents = Path.home() / "Documents" / "RecoveryAssistant"
            documents.mkdir(parents=True, exist_ok=True)
            db_path = str(documents / "receivables.db")

        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False}
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"Database initialized at: {db_path}")

    def init_database(self):
        """Create all tables"""

        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    def get_session(self) -> Session:
        """Get database session"""

        return self.SessionLocal()

    def close(self):
        """Close database connection"""

        self.engine.dispose()
        logger.info("Database connection closed")

    def backup_database(self, backup_path: str) -> bool:
        """
        Backup database to another file

        Args:
            backup_path: Path for backup file

        Returns:
            Success status
        """

        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

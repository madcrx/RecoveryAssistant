"""
Dashboard Widget

Main dashboard showing collection metrics and KPIs.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MetricCard(QFrame):
    """Card widget for displaying a metric"""

    def __init__(self, title, value, subtitle=""):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("color: #333; font-size: 28px; font-weight: bold;")
        layout.addWidget(value_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #999; font-size: 11px;")
            layout.addWidget(subtitle_label)


class DashboardWidget(QWidget):
    """Dashboard view with metrics"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup dashboard UI"""
        main_layout = QVBoxLayout(self)

        # Title
        title = QLabel("📊 Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        main_layout.addWidget(title)

        # Metrics grid
        self.metrics_layout = QGridLayout()
        self.metrics_layout.setSpacing(15)

        # Create metric cards (will be populated in refresh)
        self.total_outstanding_card = MetricCard("Total Outstanding", "$0.00")
        self.metrics_layout.addWidget(self.total_outstanding_card, 0, 0)

        self.invoice_count_card = MetricCard("Open Invoices", "0")
        self.metrics_layout.addWidget(self.invoice_count_card, 0, 1)

        self.customer_count_card = MetricCard("Customers", "0")
        self.metrics_layout.addWidget(self.customer_count_card, 0, 2)

        self.avg_days_card = MetricCard("Avg Days Outstanding", "0")
        self.metrics_layout.addWidget(self.avg_days_card, 1, 0)

        self.overdue_count_card = MetricCard("Overdue Invoices", "0", "60+ days")
        self.metrics_layout.addWidget(self.overdue_count_card, 1, 1)

        self.collection_rate_card = MetricCard("Collection Rate", "0%", "Last 30 days")
        self.metrics_layout.addWidget(self.collection_rate_card, 1, 2)

        main_layout.addLayout(self.metrics_layout)

        # Aging distribution
        aging_label = QLabel("Aging Distribution")
        aging_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 20px;")
        main_layout.addWidget(aging_label)

        self.aging_frame = QFrame()
        self.aging_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.aging_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        self.aging_layout = QVBoxLayout(self.aging_frame)
        main_layout.addWidget(self.aging_frame)

        main_layout.addStretch()

    def refresh(self):
        """Refresh dashboard data"""
        try:
            from ..models.database import Invoice, Customer, InvoiceStatus

            session = self.db_manager.get_session()

            # Total outstanding
            total_outstanding = session.query(
                Invoice
            ).filter(
                Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
            ).with_entities(
                Invoice.amount_outstanding
            ).all()

            total = sum(inv.amount_outstanding for inv in total_outstanding)

            # Update cards
            self.total_outstanding_card.deleteLater()
            self.total_outstanding_card = MetricCard("Total Outstanding", f"${total:,.2f}")
            self.metrics_layout.addWidget(self.total_outstanding_card, 0, 0)

            # Invoice count
            invoice_count = session.query(Invoice).filter(
                Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
            ).count()

            self.invoice_count_card.deleteLater()
            self.invoice_count_card = MetricCard("Open Invoices", str(invoice_count))
            self.metrics_layout.addWidget(self.invoice_count_card, 0, 1)

            # Customer count
            customer_count = session.query(Customer).count()

            self.customer_count_card.deleteLater()
            self.customer_count_card = MetricCard("Customers", str(customer_count))
            self.metrics_layout.addWidget(self.customer_count_card, 0, 2)

            # Average days outstanding
            invoices = session.query(Invoice).filter(
                Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
            ).all()

            if invoices:
                avg_days = sum(inv.days_outstanding for inv in invoices) / len(invoices)
            else:
                avg_days = 0

            self.avg_days_card.deleteLater()
            self.avg_days_card = MetricCard("Avg Days Outstanding", f"{avg_days:.0f}")
            self.metrics_layout.addWidget(self.avg_days_card, 1, 0)

            # Overdue count (60+ days)
            overdue_count = session.query(Invoice).filter(
                Invoice.days_outstanding >= 60,
                Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE])
            ).count()

            self.overdue_count_card.deleteLater()
            self.overdue_count_card = MetricCard("Overdue Invoices", str(overdue_count), "60+ days")
            self.metrics_layout.addWidget(self.overdue_count_card, 1, 1)

            # Collection rate - Calculate based on paid vs total invoices
            total_invoices_all = session.query(Invoice).count()
            paid_invoices_all = session.query(Invoice).filter(Invoice.status == InvoiceStatus.PAID).count()

            if total_invoices_all > 0:
                collection_rate = (paid_invoices_all / total_invoices_all) * 100
                collection_subtitle = f"{paid_invoices_all} of {total_invoices_all} collected"
            else:
                collection_rate = 0
                collection_subtitle = "No invoices yet"

            self.collection_rate_card.deleteLater()
            self.collection_rate_card = MetricCard(
                "Collection Rate",
                f"{collection_rate:.1f}%",
                collection_subtitle
            )
            self.metrics_layout.addWidget(self.collection_rate_card, 1, 2)

            # Aging distribution
            from ..models.database import AgingBucket

            aging_data = {}
            for bucket in AgingBucket:
                count = session.query(Invoice).filter(
                    Invoice.aging_bucket == bucket,
                    Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
                ).count()

                amount = sum(
                    inv.amount_outstanding for inv in
                    session.query(Invoice).filter(
                        Invoice.aging_bucket == bucket,
                        Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
                    ).all()
                )

                aging_data[bucket.value] = {'count': count, 'amount': amount}

            # Clear aging layout
            for i in reversed(range(self.aging_layout.count())):
                self.aging_layout.itemAt(i).widget().setParent(None)

            # Add aging rows
            for bucket_name, data in aging_data.items():
                row = QHBoxLayout()

                label = QLabel(f"{bucket_name}:")
                label.setMinimumWidth(100)
                row.addWidget(label)

                count_label = QLabel(f"{data['count']} invoices")
                count_label.setMinimumWidth(120)
                row.addWidget(count_label)

                amount_label = QLabel(f"${data['amount']:,.2f}")
                amount_label.setStyleSheet("font-weight: bold;")
                row.addWidget(amount_label)

                row.addStretch()

                self.aging_layout.addLayout(row)

            session.close()

            logger.info("Dashboard refreshed successfully")

        except Exception as e:
            logger.error(f"Failed to refresh dashboard: {e}")

            # Show error message
            error_label = QLabel(f"Error loading dashboard: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.aging_layout.addWidget(error_label)

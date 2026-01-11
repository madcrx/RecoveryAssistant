"""
Invoice View Widget

Invoice management and tracking.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class InvoiceWidget(QWidget):
    """Invoice management view"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup invoice view UI"""
        layout = QVBoxLayout(self)

        # Title and filters
        header = QHBoxLayout()

        title = QLabel("📄 Invoices")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search invoice number or customer...")
        self.search_box.setMaximumWidth(250)
        self.search_box.textChanged.connect(self.refresh)
        header.addWidget(self.search_box)

        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Open", "Overdue", "Partially Paid", "Paid"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.status_filter)

        # Aging filter
        self.aging_filter = QComboBox()
        self.aging_filter.addItems(["All Aging", "Current", "0-30 Days", "31-60 Days", "61-90 Days", "90+ Days"])
        self.aging_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.aging_filter)

        layout.addLayout(header)

        # Invoice table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Invoice #", "Customer", "Invoice Date", "Due Date",
            "Original Amount", "Outstanding", "Days", "Status"
        ])

        # Make table look nice
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.table)

        # Summary
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self.summary_label)

    def refresh(self):
        """Refresh invoice list"""
        try:
            from ..models.database import Invoice, Customer, InvoiceStatus, AgingBucket

            session = self.db_manager.get_session()

            # Build query
            query = session.query(Invoice).join(Customer)

            # Apply status filter
            status_text = self.status_filter.currentText()
            if status_text != "All Status":
                status_map = {
                    "Open": InvoiceStatus.OPEN,
                    "Overdue": InvoiceStatus.OVERDUE,
                    "Partially Paid": InvoiceStatus.PARTIALLY_PAID,
                    "Paid": InvoiceStatus.PAID,
                }
                if status_text in status_map:
                    query = query.filter(Invoice.status == status_map[status_text])

            # Apply aging filter
            aging_text = self.aging_filter.currentText()
            if aging_text != "All Aging":
                aging_map = {
                    "Current": AgingBucket.CURRENT,
                    "0-30 Days": AgingBucket.DAYS_0_30,
                    "31-60 Days": AgingBucket.DAYS_31_60,
                    "61-90 Days": AgingBucket.DAYS_61_90,
                    "90+ Days": AgingBucket.DAYS_90_PLUS,
                }
                if aging_text in aging_map:
                    query = query.filter(Invoice.aging_bucket == aging_map[aging_text])

            # Apply search
            search_text = self.search_box.text().strip()
            if search_text:
                query = query.filter(
                    (Invoice.invoice_number.ilike(f"%{search_text}%")) |
                    (Customer.company_name.ilike(f"%{search_text}%"))
                )

            # Get invoices
            invoices = query.order_by(Invoice.days_outstanding.desc()).all()

            # Populate table
            self.table.setRowCount(len(invoices))

            total_outstanding = 0.0

            for row, invoice in enumerate(invoices):
                # Invoice number
                self.table.setItem(row, 0, QTableWidgetItem(invoice.invoice_number))

                # Customer
                self.table.setItem(row, 1, QTableWidgetItem(invoice.customer.company_name))

                # Invoice date
                date_str = invoice.invoice_date.strftime("%Y-%m-%d") if invoice.invoice_date else "N/A"
                self.table.setItem(row, 2, QTableWidgetItem(date_str))

                # Due date
                due_str = invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "N/A"
                self.table.setItem(row, 3, QTableWidgetItem(due_str))

                # Original amount
                orig_item = QTableWidgetItem(f"${invoice.original_amount:,.2f}")
                orig_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, 4, orig_item)

                # Outstanding
                out_item = QTableWidgetItem(f"${invoice.amount_outstanding:,.2f}")
                out_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                # Color code by aging
                if invoice.days_outstanding > 90:
                    out_item.setBackground(Qt.GlobalColor.red)
                    out_item.setForeground(Qt.GlobalColor.white)
                elif invoice.days_outstanding > 60:
                    out_item.setBackground(Qt.GlobalColor.yellow)
                elif invoice.days_outstanding > 30:
                    out_item.setBackground(Qt.GlobalColor.lightGray)

                self.table.setItem(row, 5, out_item)

                # Days outstanding
                days_item = QTableWidgetItem(str(invoice.days_outstanding))
                days_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 6, days_item)

                # Status
                status_item = QTableWidgetItem(invoice.status.value)
                self.table.setItem(row, 7, status_item)

                total_outstanding += invoice.amount_outstanding

            # Update summary
            self.summary_label.setText(
                f"Showing {len(invoices)} invoices | Total Outstanding: ${total_outstanding:,.2f}"
            )

            session.close()
            logger.info(f"Invoice view refreshed: {len(invoices)} invoices")

        except Exception as e:
            logger.error(f"Failed to refresh invoice view: {e}")
            self.summary_label.setText(f"Error loading invoices: {str(e)}")
            self.summary_label.setStyleSheet("color: red;")

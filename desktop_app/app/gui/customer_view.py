"""
Customer View Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QLineEdit, QHeaderView
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class CustomerWidget(QWidget):
    """Customer management view"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup customer view UI"""
        layout = QVBoxLayout(self)

        # Title and search
        header = QHBoxLayout()

        title = QLabel("👥 Customers")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search customer name or email...")
        self.search_box.setMaximumWidth(300)
        self.search_box.textChanged.connect(self.refresh)
        header.addWidget(self.search_box)

        layout.addLayout(header)

        # Customer table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Customer ID", "Company Name", "Email", "Phone",
            "Open Invoices", "Current Balance", "Payment Score"
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
        """Refresh customer list"""
        try:
            from ..models.database import Customer, Invoice, InvoiceStatus
            from sqlalchemy import func

            session = self.db_manager.get_session()

            # Build query
            query = session.query(Customer)

            # Apply search
            search_text = self.search_box.text().strip()
            if search_text:
                query = query.filter(
                    (Customer.company_name.ilike(f"%{search_text}%")) |
                    (Customer.email.ilike(f"%{search_text}%")) |
                    (Customer.customer_id.ilike(f"%{search_text}%"))
                )

            # Get customers
            customers = query.order_by(Customer.current_balance.desc()).all()

            # Populate table
            self.table.setRowCount(len(customers))

            total_balance = 0.0

            for row, customer in enumerate(customers):
                # Customer ID
                self.table.setItem(row, 0, QTableWidgetItem(customer.customer_id or "N/A"))

                # Company name
                self.table.setItem(row, 1, QTableWidgetItem(customer.company_name))

                # Email
                self.table.setItem(row, 2, QTableWidgetItem(customer.email or "N/A"))

                # Phone
                self.table.setItem(row, 3, QTableWidgetItem(customer.phone or "N/A"))

                # Count open invoices
                open_count = session.query(Invoice).filter(
                    Invoice.customer_id == customer.id,
                    Invoice.status.in_([InvoiceStatus.OPEN, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIALLY_PAID])
                ).count()

                count_item = QTableWidgetItem(str(open_count))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 4, count_item)

                # Current balance
                balance_item = QTableWidgetItem(f"${customer.current_balance:,.2f}")
                balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                # Color code by balance
                if customer.current_balance > 50000:
                    balance_item.setBackground(Qt.GlobalColor.red)
                    balance_item.setForeground(Qt.GlobalColor.white)
                elif customer.current_balance > 10000:
                    balance_item.setBackground(Qt.GlobalColor.yellow)

                self.table.setItem(row, 5, balance_item)

                # Payment score (simplified calculation)
                score = customer.payment_score if customer.payment_score else "N/A"
                score_item = QTableWidgetItem(str(score))
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if isinstance(score, (int, float)):
                    if score >= 80:
                        score_item.setForeground(Qt.GlobalColor.darkGreen)
                    elif score >= 60:
                        score_item.setForeground(Qt.GlobalColor.darkYellow)
                    else:
                        score_item.setForeground(Qt.GlobalColor.red)

                self.table.setItem(row, 6, score_item)

                total_balance += customer.current_balance

            # Update summary
            self.summary_label.setText(
                f"Showing {len(customers)} customers | Total Outstanding: ${total_balance:,.2f}"
            )

            session.close()
            logger.info(f"Customer view refreshed: {len(customers)} customers")

        except Exception as e:
            logger.error(f"Failed to refresh customer view: {e}")
            self.summary_label.setText(f"Error loading customers: {str(e)}")
            self.summary_label.setStyleSheet("color: red;")

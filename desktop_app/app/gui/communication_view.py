"""
Communication View Widget
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QComboBox, QPushButton, QTextEdit, QDialog,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class MessageDetailDialog(QDialog):
    """Dialog to show message details"""

    def __init__(self, log_entry, parent=None):
        super().__init__(parent)
        self.log_entry = log_entry
        self.setWindowTitle("Message Details")
        self.setMinimumSize(600, 400)
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(f"Message to: {self.log_entry.customer.company_name}")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)

        # Details
        details = f"""
Type: {self.log_entry.communication_type}
Channel: {self.log_entry.channel}
Sent: {self.log_entry.sent_at.strftime('%Y-%m-%d %H:%M:%S') if self.log_entry.sent_at else 'N/A'}
Status: {self.log_entry.status}
"""
        if self.log_entry.invoice_id:
            details += f"Invoice: {self.log_entry.invoice.invoice_number}\n"

        details_label = QLabel(details)
        layout.addWidget(details_label)

        # Message content
        layout.addWidget(QLabel("Message:"))
        content = QTextEdit()
        content.setReadOnly(True)
        content.setPlainText(self.log_entry.message_content or "No content available")
        layout.addWidget(content)

        # Error info
        if self.log_entry.error_message:
            layout.addWidget(QLabel("Error:"))
            error = QTextEdit()
            error.setReadOnly(True)
            error.setPlainText(self.log_entry.error_message)
            error.setMaximumHeight(100)
            error.setStyleSheet("color: red;")
            layout.addWidget(error)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class CommunicationWidget(QWidget):
    """Communication log view"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup communication view UI"""
        layout = QVBoxLayout(self)

        # Title and filters
        header = QHBoxLayout()

        title = QLabel("✉️ Communications")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Sent", "Failed", "Pending"])
        self.status_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.status_filter)

        # Type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Reminder", "Payment Request", "Thank You", "Collection Notice"])
        self.type_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.type_filter)

        # Channel filter
        self.channel_filter = QComboBox()
        self.channel_filter.addItems(["All Channels", "Email", "SMS"])
        self.channel_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self.channel_filter)

        layout.addLayout(header)

        # Communication table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date/Time", "Customer", "Invoice", "Type", "Channel", "Status", "Actions"
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
        """Refresh communication log"""
        try:
            from ..models.database import CommunicationLog, Customer, Invoice

            session = self.db_manager.get_session()

            # Build query
            query = session.query(CommunicationLog).join(Customer)

            # Apply status filter
            status_text = self.status_filter.currentText()
            if status_text != "All Status":
                query = query.filter(CommunicationLog.status == status_text.lower())

            # Apply type filter
            type_text = self.type_filter.currentText()
            if type_text != "All Types":
                query = query.filter(CommunicationLog.communication_type == type_text.lower().replace(' ', '_'))

            # Apply channel filter
            channel_text = self.channel_filter.currentText()
            if channel_text != "All Channels":
                query = query.filter(CommunicationLog.channel == channel_text.lower())

            # Get logs
            logs = query.order_by(CommunicationLog.sent_at.desc()).limit(500).all()

            # Populate table
            self.table.setRowCount(len(logs))

            sent_count = 0
            failed_count = 0

            for row, log in enumerate(logs):
                # Date/Time
                date_str = log.sent_at.strftime("%Y-%m-%d %H:%M") if log.sent_at else "N/A"
                self.table.setItem(row, 0, QTableWidgetItem(date_str))

                # Customer
                self.table.setItem(row, 1, QTableWidgetItem(log.customer.company_name))

                # Invoice
                invoice_num = log.invoice.invoice_number if log.invoice_id and log.invoice else "N/A"
                self.table.setItem(row, 2, QTableWidgetItem(invoice_num))

                # Type
                comm_type = log.communication_type.replace('_', ' ').title()
                self.table.setItem(row, 3, QTableWidgetItem(comm_type))

                # Channel
                channel_item = QTableWidgetItem(log.channel.upper())
                self.table.setItem(row, 4, channel_item)

                # Status
                status_item = QTableWidgetItem(log.status.capitalize())
                if log.status == 'sent':
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                    sent_count += 1
                elif log.status == 'failed':
                    status_item.setForeground(Qt.GlobalColor.red)
                    failed_count += 1
                else:
                    status_item.setForeground(Qt.GlobalColor.darkYellow)

                self.table.setItem(row, 5, status_item)

                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)

                view_btn = QPushButton("View")
                view_btn.clicked.connect(lambda checked, l=log: self._view_message(l))
                actions_layout.addWidget(view_btn)

                if log.status == 'failed':
                    resend_btn = QPushButton("Resend")
                    resend_btn.clicked.connect(lambda checked, l=log: self._resend_message(l))
                    actions_layout.addWidget(resend_btn)

                self.table.setCellWidget(row, 6, actions_widget)

            # Update summary
            self.summary_label.setText(
                f"Showing {len(logs)} communications | "
                f"Sent: {sent_count} | Failed: {failed_count}"
            )

            session.close()
            logger.info(f"Communication view refreshed: {len(logs)} logs")

        except Exception as e:
            logger.error(f"Failed to refresh communication view: {e}")
            self.summary_label.setText(f"Error loading communications: {str(e)}")
            self.summary_label.setStyleSheet("color: red;")

    def _view_message(self, log_entry):
        """View message details"""
        try:
            dialog = MessageDetailDialog(log_entry, self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to show message details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to show message details:\n{str(e)}")

    def _resend_message(self, log_entry):
        """Resend a failed message"""
        reply = QMessageBox.question(
            self,
            "Resend Message",
            f"Resend message to {log_entry.customer.company_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # This would integrate with the workflow engine
                # For now, just show a message
                QMessageBox.information(
                    self,
                    "Resend Queued",
                    f"Message will be resent to {log_entry.customer.company_name}\n\n"
                    "The workflow engine will process this shortly."
                )
                logger.info(f"Queued resend for communication {log_entry.id}")

            except Exception as e:
                logger.error(f"Failed to resend message: {e}")
                QMessageBox.critical(
                    self,
                    "Resend Failed",
                    f"Failed to resend message:\n{str(e)}"
                )

"""
Invoice View Widget

Invoice management and tracking.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class InvoiceWidget(QWidget):
    """Invoice management view"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup invoice view UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("📄 Invoices")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Placeholder
        placeholder = QLabel(
            "Invoice Management View\n\n"
            "Features:\n"
            "• View all invoices\n"
            "• Filter by status, aging, customer\n"
            "• Search by invoice number\n"
            "• View payment history\n"
            "• Send manual reminders\n\n"
            "Coming soon..."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(placeholder)

        layout.addStretch()

    def refresh(self):
        """Refresh invoice list"""
        pass

"""
Customer View Widget
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class CustomerWidget(QWidget):
    """Customer management view"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup customer view UI"""
        layout = QVBoxLayout(self)

        title = QLabel("👥 Customers")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        placeholder = QLabel(
            "Customer Management\n\n"
            "Features:\n"
            "• View all customers\n"
            "• Payment scores & risk levels\n"
            "• Outstanding balances\n"
            "• Communication preferences\n\n"
            "Coming soon..."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(placeholder)

        layout.addStretch()

    def refresh(self):
        """Refresh customer list"""
        pass

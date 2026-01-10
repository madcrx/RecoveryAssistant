"""
Dashboard Widget

Main dashboard showing collection metrics and KPIs.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class DashboardWidget(QWidget):
    """Dashboard view with metrics"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup dashboard UI"""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("📊 Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Placeholder content
        placeholder = QLabel(
            "Dashboard View\n\n"
            "This will show:\n"
            "• Total Outstanding Receivables\n"
            "• Collection Rate (30-day)\n"
            "• Payments This Month\n"
            "• Average Days to Payment\n"
            "• Aging Distribution Chart\n"
            "• High-Risk Customer Count\n\n"
            "Coming soon..."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(placeholder)

        layout.addStretch()

    def refresh(self):
        """Refresh dashboard data"""
        # TODO: Load actual data from database
        pass

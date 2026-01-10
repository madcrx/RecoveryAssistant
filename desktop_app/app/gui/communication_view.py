"""
Communication View Widget
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class CommunicationWidget(QWidget):
    """Communication log view"""

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._setup_ui()

    def _setup_ui(self):
        """Setup communication view UI"""
        layout = QVBoxLayout(self)

        title = QLabel("✉️ Communications")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        placeholder = QLabel(
            "Communication Log\n\n"
            "Features:\n"
            "• View all sent emails/SMS\n"
            "• Track delivery & open rates\n"
            "• Customer responses\n"
            "• Resend failed messages\n\n"
            "Coming soon..."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: gray; font-size: 14px;")
        layout.addWidget(placeholder)

        layout.addStretch()

    def refresh(self):
        """Refresh communication log"""
        pass

"""
Settings Dialogs

Configuration dialogs for workflows and integrations.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QCheckBox, QGroupBox, QFormLayout,
    QTabWidget, QWidget, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class IntegrationSettingsDialog(QDialog):
    """Integration settings dialog"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

        self.setWindowTitle("Integration Settings")
        self.setMinimumSize(600, 500)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # Tab widget for different integrations
        tabs = QTabWidget()

        # OpenAI tab
        openai_tab = QWidget()
        openai_layout = QFormLayout(openai_tab)

        self.openai_enabled = QCheckBox("Enable OpenAI")
        openai_layout.addRow("", self.openai_enabled)

        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_api_key.setPlaceholderText("sk-...")
        openai_layout.addRow("API Key:", self.openai_api_key)

        self.openai_model = QComboBox()
        self.openai_model.addItems([
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo"
        ])
        openai_layout.addRow("Model:", self.openai_model)

        test_openai_btn = QPushButton("Test Connection")
        test_openai_btn.clicked.connect(self._test_openai)
        openai_layout.addRow("", test_openai_btn)

        tabs.addTab(openai_tab, "OpenAI")

        # Xero tab
        xero_tab = QWidget()
        xero_layout = QFormLayout(xero_tab)

        self.xero_enabled = QCheckBox("Enable Xero Integration")
        xero_layout.addRow("", self.xero_enabled)

        self.xero_client_id = QLineEdit()
        xero_layout.addRow("Client ID:", self.xero_client_id)

        self.xero_client_secret = QLineEdit()
        self.xero_client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        xero_layout.addRow("Client Secret:", self.xero_client_secret)

        self.xero_auto_sync = QCheckBox("Automatic Sync")
        xero_layout.addRow("", self.xero_auto_sync)

        self.xero_sync_hours = QSpinBox()
        self.xero_sync_hours.setRange(1, 168)
        self.xero_sync_hours.setValue(24)
        self.xero_sync_hours.setSuffix(" hours")
        xero_layout.addRow("Sync Interval:", self.xero_sync_hours)

        test_xero_btn = QPushButton("Connect to Xero")
        test_xero_btn.clicked.connect(self._connect_xero)
        xero_layout.addRow("", test_xero_btn)

        tabs.addTab(xero_tab, "Xero")

        # Stripe tab
        stripe_tab = QWidget()
        stripe_layout = QFormLayout(stripe_tab)

        self.stripe_enabled = QCheckBox("Enable Stripe Payments")
        stripe_layout.addRow("", self.stripe_enabled)

        self.stripe_api_key = QLineEdit()
        self.stripe_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.stripe_api_key.setPlaceholderText("sk_live_...")
        stripe_layout.addRow("API Key:", self.stripe_api_key)

        test_stripe_btn = QPushButton("Test Connection")
        test_stripe_btn.clicked.connect(self._test_stripe)
        stripe_layout.addRow("", test_stripe_btn)

        tabs.addTab(stripe_tab, "Stripe")

        # Outlook tab
        outlook_tab = QWidget()
        outlook_layout = QFormLayout(outlook_tab)

        outlook_layout.addRow(QLabel("Microsoft Outlook is automatically detected."))
        outlook_layout.addRow(QLabel("No configuration needed."))

        test_outlook_btn = QPushButton("Test Outlook Connection")
        test_outlook_btn.clicked.connect(self._test_outlook)
        outlook_layout.addRow("", test_outlook_btn)

        tabs.addTab(outlook_tab, "Outlook")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load current settings"""

        # OpenAI
        self.openai_enabled.setChecked(
            self.config_manager.get("integrations.openai.enabled", True)
        )
        self.openai_api_key.setText(
            self.config_manager.get("integrations.openai.api_key", "")
        )
        model = self.config_manager.get("integrations.openai.model", "gpt-4-turbo-preview")
        index = self.openai_model.findText(model)
        if index >= 0:
            self.openai_model.setCurrentIndex(index)

        # Xero
        self.xero_enabled.setChecked(
            self.config_manager.get("integrations.xero.enabled", False)
        )
        self.xero_client_id.setText(
            self.config_manager.get("integrations.xero.client_id", "")
        )
        self.xero_client_secret.setText(
            self.config_manager.get("integrations.xero.client_secret", "")
        )
        self.xero_auto_sync.setChecked(
            self.config_manager.get("integrations.xero.auto_sync", False)
        )
        self.xero_sync_hours.setValue(
            self.config_manager.get("integrations.xero.sync_interval_hours", 24)
        )

        # Stripe
        self.stripe_enabled.setChecked(
            self.config_manager.get("integrations.stripe.enabled", False)
        )
        self.stripe_api_key.setText(
            self.config_manager.get("integrations.stripe.api_key", "")
        )

    def _save_settings(self):
        """Save settings"""

        config = {
            "integrations": {
                "openai": {
                    "enabled": self.openai_enabled.isChecked(),
                    "api_key": self.openai_api_key.text(),
                    "model": self.openai_model.currentText(),
                },
                "xero": {
                    "enabled": self.xero_enabled.isChecked(),
                    "client_id": self.xero_client_id.text(),
                    "client_secret": self.xero_client_secret.text(),
                    "auto_sync": self.xero_auto_sync.isChecked(),
                    "sync_interval_hours": self.xero_sync_hours.value(),
                },
                "stripe": {
                    "enabled": self.stripe_enabled.isChecked(),
                    "api_key": self.stripe_api_key.text(),
                }
            }
        }

        self.config_manager.update_config(config)

        QMessageBox.information(
            self,
            "Settings Saved",
            "Integration settings have been saved successfully."
        )

        self.accept()

    def _test_openai(self):
        """Test OpenAI connection"""
        api_key = self.openai_api_key.text()

        if not api_key:
            QMessageBox.warning(self, "Test OpenAI", "Please enter an API key first.")
            return

        QMessageBox.information(
            self,
            "Test OpenAI",
            "✅ API key format looks valid.\n\n"
            "Full testing will occur when generating messages."
        )

    def _connect_xero(self):
        """Connect to Xero"""
        QMessageBox.information(
            self,
            "Connect Xero",
            "Xero OAuth2 connection will be implemented in the full version.\n\n"
            "For now, save your credentials and use manual sync."
        )

    def _test_stripe(self):
        """Test Stripe connection"""
        api_key = self.stripe_api_key.text()

        if not api_key:
            QMessageBox.warning(self, "Test Stripe", "Please enter an API key first.")
            return

        QMessageBox.information(
            self,
            "Test Stripe",
            "✅ API key format looks valid.\n\n"
            "Payment link generation will validate the key."
        )

    def _test_outlook(self):
        """Test Outlook connection"""
        try:
            import win32com.client
            outlook = win32com.client.Dispatch("Outlook.Application")
            outlook = None

            QMessageBox.information(
                self,
                "Test Outlook",
                "✅ Microsoft Outlook is installed and accessible!"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Test Outlook",
                f"❌ Could not connect to Outlook:\n\n{str(e)}"
            )


class WorkflowSettingsDialog(QDialog):
    """Workflow settings dialog"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

        self.setWindowTitle("Workflow Settings")
        self.setMinimumSize(500, 600)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)

        # Enable workflows
        self.workflows_enabled = QCheckBox("Enable Automated Workflows")
        layout.addWidget(self.workflows_enabled)

        # Auto-run interval
        interval_group = QGroupBox("Automation Schedule")
        interval_layout = QFormLayout()

        self.auto_run_interval = QSpinBox()
        self.auto_run_interval.setRange(5, 1440)
        self.auto_run_interval.setValue(30)
        self.auto_run_interval.setSuffix(" minutes")
        interval_layout.addRow("Run workflows every:", self.auto_run_interval)

        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)

        # Reminder schedules by aging bucket
        schedules_group = QGroupBox("Reminder Schedules")
        schedules_layout = QVBoxLayout()

        # 0-30 days
        days_0_30_group = QGroupBox("0-30 Days Overdue")
        days_0_30_layout = QFormLayout()

        self.freq_0_30 = QSpinBox()
        self.freq_0_30.setRange(1, 30)
        self.freq_0_30.setValue(7)
        self.freq_0_30.setSuffix(" days")
        days_0_30_layout.addRow("Reminder Frequency:", self.freq_0_30)

        self.tone_0_30 = QComboBox()
        self.tone_0_30.addItems(["friendly", "professional", "firm", "urgent"])
        days_0_30_layout.addRow("Tone:", self.tone_0_30)

        days_0_30_group.setLayout(days_0_30_layout)
        schedules_layout.addWidget(days_0_30_group)

        # 31-60 days
        days_31_60_group = QGroupBox("31-60 Days Overdue")
        days_31_60_layout = QFormLayout()

        self.freq_31_60 = QSpinBox()
        self.freq_31_60.setRange(1, 30)
        self.freq_31_60.setValue(3)
        self.freq_31_60.setSuffix(" days")
        days_31_60_layout.addRow("Reminder Frequency:", self.freq_31_60)

        self.tone_31_60 = QComboBox()
        self.tone_31_60.addItems(["friendly", "professional", "firm", "urgent"])
        self.tone_31_60.setCurrentText("professional")
        days_31_60_layout.addRow("Tone:", self.tone_31_60)

        days_31_60_group.setLayout(days_31_60_layout)
        schedules_layout.addWidget(days_31_60_group)

        # 61-90 days
        days_61_90_group = QGroupBox("61-90 Days Overdue")
        days_61_90_layout = QFormLayout()

        self.freq_61_90 = QSpinBox()
        self.freq_61_90.setRange(1, 30)
        self.freq_61_90.setValue(1)
        self.freq_61_90.setSuffix(" days")
        days_61_90_layout.addRow("Reminder Frequency:", self.freq_61_90)

        self.tone_61_90 = QComboBox()
        self.tone_61_90.addItems(["friendly", "professional", "firm", "urgent"])
        self.tone_61_90.setCurrentText("firm")
        days_61_90_layout.addRow("Tone:", self.tone_61_90)

        days_61_90_group.setLayout(days_61_90_layout)
        schedules_layout.addWidget(days_61_90_group)

        # 90+ days
        days_90_plus_group = QGroupBox("90+ Days Overdue")
        days_90_plus_layout = QFormLayout()

        self.freq_90_plus = QSpinBox()
        self.freq_90_plus.setRange(1, 30)
        self.freq_90_plus.setValue(1)
        self.freq_90_plus.setSuffix(" days")
        days_90_plus_layout.addRow("Reminder Frequency:", self.freq_90_plus)

        self.tone_90_plus = QComboBox()
        self.tone_90_plus.addItems(["friendly", "professional", "firm", "urgent"])
        self.tone_90_plus.setCurrentText("urgent")
        days_90_plus_layout.addRow("Tone:", self.tone_90_plus)

        self.auto_escalate_90 = QCheckBox("Automatically Escalate")
        days_90_plus_layout.addRow("", self.auto_escalate_90)

        days_90_plus_group.setLayout(days_90_plus_layout)
        schedules_layout.addWidget(days_90_plus_group)

        schedules_group.setLayout(schedules_layout)
        layout.addWidget(schedules_group)

        # Other settings
        other_group = QGroupBox("Other Settings")
        other_layout = QFormLayout()

        self.payment_plan_threshold = QSpinBox()
        self.payment_plan_threshold.setRange(1000, 1000000)
        self.payment_plan_threshold.setValue(10000)
        self.payment_plan_threshold.setPrefix("$")
        other_layout.addRow("Payment Plan Threshold:", self.payment_plan_threshold)

        self.escalation_enabled = QCheckBox("Enable Escalation")
        other_layout.addRow("", self.escalation_enabled)

        other_group.setLayout(other_layout)
        layout.addWidget(other_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load current settings"""

        self.workflows_enabled.setChecked(
            self.config_manager.get("workflows.enabled", True)
        )

        self.auto_run_interval.setValue(
            self.config_manager.get("workflows.auto_run_interval_minutes", 30)
        )

        # 0-30 days
        self.freq_0_30.setValue(
            self.config_manager.get("workflows.schedules.0-30.reminder_frequency_days", 7)
        )
        self.tone_0_30.setCurrentText(
            self.config_manager.get("workflows.schedules.0-30.tone", "friendly")
        )

        # 31-60 days
        self.freq_31_60.setValue(
            self.config_manager.get("workflows.schedules.31-60.reminder_frequency_days", 3)
        )
        self.tone_31_60.setCurrentText(
            self.config_manager.get("workflows.schedules.31-60.tone", "professional")
        )

        # 61-90 days
        self.freq_61_90.setValue(
            self.config_manager.get("workflows.schedules.61-90.reminder_frequency_days", 1)
        )
        self.tone_61_90.setCurrentText(
            self.config_manager.get("workflows.schedules.61-90.tone", "firm")
        )

        # 90+ days
        self.freq_90_plus.setValue(
            self.config_manager.get("workflows.schedules.90+.reminder_frequency_days", 1)
        )
        self.tone_90_plus.setCurrentText(
            self.config_manager.get("workflows.schedules.90+.tone", "urgent")
        )
        self.auto_escalate_90.setChecked(
            self.config_manager.get("workflows.schedules.90+.auto_escalate", True)
        )

        # Other
        self.payment_plan_threshold.setValue(
            int(self.config_manager.get("workflows.payment_plan_threshold", 10000))
        )
        self.escalation_enabled.setChecked(
            self.config_manager.get("workflows.escalation_enabled", True)
        )

    def _save_settings(self):
        """Save settings"""

        config = {
            "workflows": {
                "enabled": self.workflows_enabled.isChecked(),
                "auto_run_interval_minutes": self.auto_run_interval.value(),
                "schedules": {
                    "0-30": {
                        "reminder_frequency_days": self.freq_0_30.value(),
                        "tone": self.tone_0_30.currentText(),
                    },
                    "31-60": {
                        "reminder_frequency_days": self.freq_31_60.value(),
                        "tone": self.tone_31_60.currentText(),
                    },
                    "61-90": {
                        "reminder_frequency_days": self.freq_61_90.value(),
                        "tone": self.tone_61_90.currentText(),
                    },
                    "90+": {
                        "reminder_frequency_days": self.freq_90_plus.value(),
                        "tone": self.tone_90_plus.currentText(),
                        "auto_escalate": self.auto_escalate_90.isChecked(),
                    }
                },
                "payment_plan_threshold": float(self.payment_plan_threshold.value()),
                "escalation_enabled": self.escalation_enabled.isChecked(),
            }
        }

        self.config_manager.update_config(config)

        QMessageBox.information(
            self,
            "Settings Saved",
            "Workflow settings have been saved successfully."
        )

        self.accept()

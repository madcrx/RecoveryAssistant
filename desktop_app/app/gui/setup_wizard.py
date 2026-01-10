"""
Setup Wizard

First-run configuration wizard for RecoveryAssistant.
"""

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class SetupWizard(QWizard):
    """First-run setup wizard"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("RecoveryAssistant - Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 400)

        # Add pages
        self.addPage(WelcomePage())
        self.addPage(OpenAIConfigPage())
        self.addPage(OutlookConfigPage())
        self.addPage(XeroConfigPage())
        self.addPage(StripeConfigPage())
        self.addPage(CompletionPage())

        self.configuration = {}

    def get_configuration(self):
        """Get configuration data from wizard"""

        # Collect data from all pages
        config = {
            "first_run": False,
            "integrations": {
                "openai": {
                    "api_key": self.field("openai_api_key") or "",
                    "enabled": True
                },
                "xero": {
                    "enabled": self.field("xero_enabled") or False,
                    "client_id": self.field("xero_client_id") or "",
                    "client_secret": self.field("xero_client_secret") or "",
                },
                "stripe": {
                    "enabled": self.field("stripe_enabled") or False,
                    "api_key": self.field("stripe_api_key") or "",
                }
            }
        }

        return config


class WelcomePage(QWizardPage):
    """Welcome page"""

    def __init__(self):
        super().__init__()

        self.setTitle("Welcome to RecoveryAssistant")
        self.setSubTitle("This wizard will help you configure RecoveryAssistant for first use.")

        layout = QVBoxLayout()

        welcome_text = QLabel(
            "<h2>Automated Receivables Collection</h2>"
            "<p>RecoveryAssistant helps you achieve 99% collection rates through "
            "AI-powered automation, Microsoft Outlook integration, and seamless "
            "payment processing.</p>"
            "<br>"
            "<p><b>What you'll need:</b></p>"
            "<ul>"
            "<li>OpenAI API Key (Required)</li>"
            "<li>Microsoft Outlook installed (Required)</li>"
            "<li>Xero credentials (Optional)</li>"
            "<li>Stripe API key (Optional)</li>"
            "</ul>"
            "<br>"
            "<p>Click 'Next' to begin setup.</p>"
        )
        welcome_text.setWordWrap(True)

        layout.addWidget(welcome_text)
        self.setLayout(layout)


class OpenAIConfigPage(QWizardPage):
    """OpenAI API configuration page"""

    def __init__(self):
        super().__init__()

        self.setTitle("OpenAI Configuration")
        self.setSubTitle("Enter your OpenAI API key for AI-powered collection messages.")

        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "<p>RecoveryAssistant uses OpenAI GPT-4 to generate personalized, "
            "effective collection messages.</p>"
            "<br>"
            "<p><b>To get your API key:</b></p>"
            "<ol>"
            "<li>Visit: https://platform.openai.com</li>"
            "<li>Sign up or log in</li>"
            "<li>Go to API Keys section</li>"
            "<li>Create a new secret key</li>"
            "<li>Copy and paste it below</li>"
            "</ol>"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # API Key input
        layout.addWidget(QLabel("OpenAI API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.api_key_input)

        # Test button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)

        layout.addStretch()
        self.setLayout(layout)

        # Register field
        self.registerField("openai_api_key*", self.api_key_input)

    def test_connection(self):
        """Test OpenAI API connection"""
        api_key = self.api_key_input.text()

        if not api_key:
            QMessageBox.warning(self, "Test Connection", "Please enter an API key first.")
            return

        # TODO: Actually test the connection
        QMessageBox.information(
            self,
            "Test Connection",
            "✅ Connection test placeholder\n\n"
            "In production, this would verify your API key with OpenAI."
        )


class OutlookConfigPage(QWizardPage):
    """Outlook configuration page"""

    def __init__(self):
        super().__init__()

        self.setTitle("Microsoft Outlook")
        self.setSubTitle("Verify Outlook integration for sending emails.")

        layout = QVBoxLayout()

        info = QLabel(
            "<p>RecoveryAssistant sends collection emails through your local "
            "Microsoft Outlook installation.</p>"
            "<br>"
            "<p><b>Requirements:</b></p>"
            "<ul>"
            "<li>Outlook must be installed on this computer</li>"
            "<li>Outlook must be configured with your email account</li>"
            "</ul>"
            "<br>"
            "<p>Click 'Test Connection' to verify Outlook is accessible.</p>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Test button
        self.test_button = QPushButton("Test Outlook Connection")
        self.test_button.clicked.connect(self.test_outlook)
        layout.addWidget(self.test_button)

        layout.addStretch()
        self.setLayout(layout)

    def test_outlook(self):
        """Test Outlook connection"""
        try:
            import win32com.client
            outlook = win32com.client.Dispatch("Outlook.Application")
            outlook = None  # Release

            QMessageBox.information(
                self,
                "Outlook Test",
                "✅ Microsoft Outlook is installed and accessible!"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Outlook Test",
                f"❌ Could not connect to Outlook:\n\n{str(e)}\n\n"
                "Please ensure Microsoft Outlook is installed."
            )


class XeroConfigPage(QWizardPage):
    """Xero configuration page (optional)"""

    def __init__(self):
        super().__init__()

        self.setTitle("Xero Integration (Optional)")
        self.setSubTitle("Connect to Xero for automatic invoice synchronization.")

        layout = QVBoxLayout()

        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Xero Integration")
        self.enable_checkbox.toggled.connect(self.toggle_inputs)
        layout.addWidget(self.enable_checkbox)

        info = QLabel(
            "<p>Xero integration allows automatic syncing of invoices and "
            "customer data.</p>"
            "<br>"
            "<p><b>To get your credentials:</b></p>"
            "<ol>"
            "<li>Visit: https://developer.xero.com</li>"
            "<li>Create or select your app</li>"
            "<li>Copy Client ID and Client Secret</li>"
            "</ol>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Client ID
        layout.addWidget(QLabel("Client ID:"))
        self.client_id_input = QLineEdit()
        self.client_id_input.setEnabled(False)
        layout.addWidget(self.client_id_input)

        # Client Secret
        layout.addWidget(QLabel("Client Secret:"))
        self.client_secret_input = QLineEdit()
        self.client_secret_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.client_secret_input.setEnabled(False)
        layout.addWidget(self.client_secret_input)

        layout.addStretch()
        self.setLayout(layout)

        # Register fields
        self.registerField("xero_enabled", self.enable_checkbox)
        self.registerField("xero_client_id", self.client_id_input)
        self.registerField("xero_client_secret", self.client_secret_input)

    def toggle_inputs(self, enabled):
        """Enable/disable inputs based on checkbox"""
        self.client_id_input.setEnabled(enabled)
        self.client_secret_input.setEnabled(enabled)


class StripeConfigPage(QWizardPage):
    """Stripe configuration page (optional)"""

    def __init__(self):
        super().__init__()

        self.setTitle("Stripe Payment Processing (Optional)")
        self.setSubTitle("Enable payment links for easy customer payments.")

        layout = QVBoxLayout()

        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Stripe Payments")
        self.enable_checkbox.toggled.connect(self.toggle_inputs)
        layout.addWidget(self.enable_checkbox)

        info = QLabel(
            "<p>Stripe integration allows you to include secure payment links "
            "in collection emails.</p>"
            "<br>"
            "<p><b>To get your API key:</b></p>"
            "<ol>"
            "<li>Visit: https://stripe.com/dashboard</li>"
            "<li>Go to Developers → API keys</li>"
            "<li>Copy your Secret Key</li>"
            "</ol>"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # API Key
        layout.addWidget(QLabel("Stripe API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk_live_...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setEnabled(False)
        layout.addWidget(self.api_key_input)

        layout.addStretch()
        self.setLayout(layout)

        # Register fields
        self.registerField("stripe_enabled", self.enable_checkbox)
        self.registerField("stripe_api_key", self.api_key_input)

    def toggle_inputs(self, enabled):
        """Enable/disable inputs based on checkbox"""
        self.api_key_input.setEnabled(enabled)


class CompletionPage(QWizardPage):
    """Completion page"""

    def __init__(self):
        super().__init__()

        self.setTitle("Setup Complete!")
        self.setSubTitle("RecoveryAssistant is ready to use.")

        layout = QVBoxLayout()

        completion_text = QLabel(
            "<h2>You're all set!</h2>"
            "<br>"
            "<p>RecoveryAssistant has been configured successfully.</p>"
            "<br>"
            "<p><b>Next steps:</b></p>"
            "<ol>"
            "<li>Import your receivables data (PDF, CSV, or Xero sync)</li>"
            "<li>Review the imported invoices and customers</li>"
            "<li>Enable automated workflows</li>"
            "<li>Let RecoveryAssistant handle your collections!</li>"
            "</ol>"
            "<br>"
            "<p>Click 'Finish' to start using RecoveryAssistant.</p>"
        )
        completion_text.setWordWrap(True)

        layout.addWidget(completion_text)
        layout.addStretch()
        self.setLayout(layout)

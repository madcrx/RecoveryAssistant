"""
Main Application Window

The main GUI window for RecoveryAssistant Desktop.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenuBar, QMenu, QToolBar, QStatusBar,
    QPushButton, QLabel, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""

    # Signals
    import_requested = pyqtSignal(str)  # file_path
    sync_requested = pyqtSignal(str)  # integration_name

    def __init__(self, db_manager, config_manager, scheduler):
        super().__init__()

        self.db_manager = db_manager
        self.config_manager = config_manager
        self.scheduler = scheduler

        self.setWindowTitle("RecoveryAssistant - Automated Receivables Collection")
        self.setGeometry(100, 100, 1400, 900)

        self._setup_ui()
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        self._load_initial_data()

        logger.info("Main window initialized")

    def _setup_ui(self):
        """Setup main UI layout"""

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Tab widget for different views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_dashboard_tab()
        self._create_invoices_tab()
        self._create_customers_tab()
        self._create_communications_tab()
        self._create_analytics_tab()

    def _create_dashboard_tab(self):
        """Create dashboard tab"""

        from .dashboard import DashboardWidget

        self.dashboard = DashboardWidget(self.db_manager)
        self.tab_widget.addTab(self.dashboard, "📊 Dashboard")

    def _create_invoices_tab(self):
        """Create invoices tab"""

        from .invoice_view import InvoiceWidget

        self.invoices = InvoiceWidget(self.db_manager)
        self.tab_widget.addTab(self.invoices, "📄 Invoices")

    def _create_customers_tab(self):
        """Create customers tab"""

        from .customer_view import CustomerWidget

        self.customers = CustomerWidget(self.db_manager)
        self.tab_widget.addTab(self.customers, "👥 Customers")

    def _create_communications_tab(self):
        """Create communications tab"""

        from .communication_view import CommunicationWidget

        self.communications = CommunicationWidget(self.db_manager)
        self.tab_widget.addTab(self.communications, "✉️ Communications")

    def _create_analytics_tab(self):
        """Create analytics tab"""

        from .analytics_view import AnalyticsWidget

        self.analytics = AnalyticsWidget(self.db_manager)
        self.tab_widget.addTab(self.analytics, "📈 Analytics")

    def _create_menu_bar(self):
        """Create menu bar"""

        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        import_pdf_action = QAction("Import PDF...", self)
        import_pdf_action.triggered.connect(self._import_pdf)
        file_menu.addAction(import_pdf_action)

        import_csv_action = QAction("Import CSV...", self)
        import_csv_action.triggered.connect(self._import_csv)
        file_menu.addAction(import_csv_action)

        file_menu.addSeparator()

        backup_action = QAction("Backup Database...", self)
        backup_action.triggered.connect(self._backup_database)
        file_menu.addAction(backup_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Integration menu
        integration_menu = menubar.addMenu("&Integrations")

        sync_xero_action = QAction("Sync with Xero", self)
        sync_xero_action.triggered.connect(lambda: self._sync_integration("xero"))
        integration_menu.addAction(sync_xero_action)

        test_outlook_action = QAction("Test Outlook Connection", self)
        test_outlook_action.triggered.connect(self._test_outlook)
        integration_menu.addAction(test_outlook_action)

        integration_menu.addSeparator()

        settings_action = QAction("Integration Settings...", self)
        settings_action.triggered.connect(self._show_integration_settings)
        integration_menu.addAction(settings_action)

        # Workflow menu
        workflow_menu = menubar.addMenu("&Workflows")

        run_workflows_action = QAction("Run Workflows Now", self)
        run_workflows_action.triggered.connect(self._run_workflows)
        workflow_menu.addAction(run_workflows_action)

        workflow_settings_action = QAction("Workflow Settings...", self)
        workflow_settings_action.triggered.connect(self._show_workflow_settings)
        workflow_menu.addAction(workflow_settings_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        user_guide_action = QAction("User Guide", self)
        user_guide_action.triggered.connect(self._show_user_guide)
        help_menu.addAction(user_guide_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """Create toolbar"""

        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Import button
        import_btn = QPushButton("📁 Import")
        import_btn.clicked.connect(self._show_import_menu)
        toolbar.addWidget(import_btn)

        toolbar.addSeparator()

        # Sync button
        sync_btn = QPushButton("🔄 Sync Xero")
        sync_btn.clicked.connect(lambda: self._sync_integration("xero"))
        toolbar.addWidget(sync_btn)

        toolbar.addSeparator()

        # Run workflows button
        workflow_btn = QPushButton("▶️ Run Workflows")
        workflow_btn.clicked.connect(self._run_workflows)
        toolbar.addWidget(workflow_btn)

        toolbar.addSeparator()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_all)
        toolbar.addWidget(refresh_btn)

    def _create_status_bar(self):
        """Create status bar"""

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status labels
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        self.status_bar.addPermanentWidget(QLabel("  |  "))

        self.connection_label = QLabel("Outlook: ✅  Xero: ❌")
        self.status_bar.addPermanentWidget(self.connection_label)

        # Update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(60000)  # Every minute

    def _load_initial_data(self):
        """Load initial data"""

        try:
            self.dashboard.refresh()
            self.invoices.refresh()
            self.customers.refresh()
            self._update_status()

            logger.info("Initial data loaded")

        except Exception as e:
            logger.error(f"Failed to load initial data: {e}")
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load some data: {e}"
            )

    def _import_pdf(self):
        """Import PDF file"""
        from .import_wizard import ImportDialog

        dialog = ImportDialog('pdf', self.db_manager, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Refresh views after import
            self._refresh_all()
            self.status_label.setText("PDF import completed")

    def _import_csv(self):
        """Import CSV file"""
        from .import_wizard import ImportDialog

        dialog = ImportDialog('csv', self.db_manager, self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            # Refresh views after import
            self._refresh_all()
            self.status_label.setText("CSV import completed")

    def _backup_database(self):
        """Backup database"""

        backup_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database Backup",
            f"receivables_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database Files (*.db)"
        )

        if backup_path:
            success = self.db_manager.backup_database(backup_path)
            if success:
                QMessageBox.information(
                    self,
                    "Backup Complete",
                    f"Database backed up successfully to:\n{backup_path}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Backup Failed",
                    "Failed to backup database"
                )

    def _sync_integration(self, integration_name: str):
        """Sync with integration"""

        logger.info(f"Syncing with {integration_name}")
        self.status_label.setText(f"Syncing with {integration_name}...")
        # TODO: Implement sync
        self.sync_requested.emit(integration_name)

    def _test_outlook(self):
        """Test Outlook connection"""

        from ..services.outlook_client import outlook_client

        if outlook_client.test_connection():
            QMessageBox.information(
                self,
                "Outlook Connection",
                "✅ Outlook connection successful!"
            )
        else:
            QMessageBox.warning(
                self,
                "Outlook Connection",
                "❌ Failed to connect to Outlook.\n\nPlease ensure Microsoft Outlook is installed and configured."
            )

    def _show_import_menu(self):
        """Show import options menu"""

        # Create context menu for import options
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        pdf_action = menu.addAction("📄 Import PDF")
        pdf_action.triggered.connect(self._import_pdf)

        csv_action = menu.addAction("📊 Import CSV")
        csv_action.triggered.connect(self._import_csv)

        menu.addSeparator()

        template_action = menu.addAction("💾 Download CSV Template")
        template_action.triggered.connect(self._download_csv_template)

        # Show menu at button position
        menu.exec(self.cursor().pos())

    def _download_csv_template(self):
        """Download CSV template"""

        from ..services.csv_import import csv_importer

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV Template",
            "receivables_template.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            if csv_importer.export_template(file_path):
                QMessageBox.information(
                    self,
                    "Template Saved",
                    f"CSV template saved to:\n{file_path}"
                )

    def _run_workflows(self):
        """Run workflows manually"""

        logger.info("Running workflows manually")
        self.status_label.setText("Running workflows...")

        try:
            from ..services.workflow_engine import get_workflow_engine

            # Run workflows in background
            engine = get_workflow_engine(self.db_manager)
            session = self.db_manager.get_session()

            result = engine.run_workflows(session)
            session.close()

            # Show results
            QMessageBox.information(
                self,
                "Workflows Complete",
                f"Workflow execution completed:\n\n"
                f"• Payment reminders sent: {result['reminders_sent']}\n"
                f"• Collection notices sent: {result['collection_notices_sent']}\n"
                f"• Thank you messages sent: {result['thank_you_sent']}\n"
                f"• Errors: {result['errors']}"
            )

            self.status_label.setText("Workflows completed")
            logger.info(f"Workflows completed: {result}")

        except Exception as e:
            logger.error(f"Failed to run workflows: {e}")
            QMessageBox.critical(
                self,
                "Workflow Error",
                f"Failed to run workflows:\n{str(e)}"
            )
            self.status_label.setText("Workflow execution failed")

    def _show_integration_settings(self):
        """Show integration settings dialog"""
        from .settings_dialogs import IntegrationSettingsDialog

        dialog = IntegrationSettingsDialog(self.config_manager, self)
        dialog.exec()

    def _show_workflow_settings(self):
        """Show workflow settings dialog"""
        from .settings_dialogs import WorkflowSettingsDialog

        dialog = WorkflowSettingsDialog(self.config_manager, self)
        dialog.exec()

    def _show_user_guide(self):
        """Show user guide"""

        guide_text = """
Recovery Assistant - User Guide

OVERVIEW
Recovery Assistant helps you manage accounts receivable and automate collection processes.

GETTING STARTED

1. Import Data
   • Go to File > Import
   • Choose PDF, CSV, or sync with Xero
   • Data will be automatically parsed and imported to database

2. View Dashboard
   • See total outstanding, open invoices, and aging metrics
   • Track collection effectiveness
   • Monitor overdue accounts

3. Manage Invoices
   • View all invoices with filters
   • Search by invoice number or customer
   • Color-coded aging indicators

4. Track Customers
   • View customer balances and payment history
   • Monitor high-risk customers
   • Track payment scores

5. Analytics & Reports
   • View detailed collection metrics
   • Analyze aging buckets
   • Identify high-risk customers
   • Export reports to Excel/CSV

6. Automated Workflows
   • Configure in Settings > Workflows
   • Automatic payment reminders for 7-30 day overdue
   • Collection notices for 90+ day overdue
   • Thank you messages for payments
   • Runs daily or trigger manually

7. Communications
   • View all sent emails and SMS
   • Track delivery status
   • Resend failed messages
   • View message history per customer

INTEGRATIONS

Xero:
  • Sync invoices automatically
  • Two-way sync of payment status
  • Configure in Settings > Integrations

Email (Outlook/Gmail):
  • Send automated reminders
  • Track open and response rates
  • Configure SMTP settings

TIPS

• Import data regularly to keep information current
• Review analytics weekly to identify trends
• Monitor high-risk customers proactively
• Customize workflow templates for your business
• Export reports for financial reviews

SUPPORT

For questions or issues:
• Check Settings > About for version info
• Review logs in the data directory
• Contact support for assistance

Version 1.0
        """

        # Show in a scrollable dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("User Guide")
        dialog.setMinimumSize(700, 600)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(guide_text)
        layout.addWidget(text_edit)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _show_about(self):
        """Show about dialog"""

        QMessageBox.about(
            self,
            "About RecoveryAssistant",
            """<h2>RecoveryAssistant Desktop</h2>
            <p>Version 1.0.0</p>
            <p>AI-Powered Automated Receivables Collection</p>
            <p>© 2024 RecoveryAssistant. All rights reserved.</p>
            <p>Achieves 99% collection rates through intelligent automation.</p>
            """
        )

    def _refresh_all(self):
        """Refresh all data"""

        logger.info("Refreshing all views")
        self.dashboard.refresh()
        self.invoices.refresh()
        self.customers.refresh()
        self.communications.refresh()
        self.analytics.refresh()
        self._update_status()

    def _update_status(self):
        """Update status bar"""

        # Update connection status
        outlook_status = "✅" if self._check_outlook_connection() else "❌"
        xero_status = "✅" if self._check_xero_connection() else "❌"

        self.connection_label.setText(
            f"Outlook: {outlook_status}  Xero: {xero_status}"
        )

    def _check_outlook_connection(self) -> bool:
        """Check Outlook connection"""

        try:
            from ..services.outlook_client import outlook_client
            return outlook_client.test_connection()
        except:
            return False

    def _check_xero_connection(self) -> bool:
        """Check Xero connection"""

        try:
            from ..services.xero_client import xero_client
            return xero_client.is_connected()
        except:
            return False

    def closeEvent(self, event):
        """Handle window close event"""

        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit RecoveryAssistant?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Application closing")
            event.accept()
        else:
            event.ignore()

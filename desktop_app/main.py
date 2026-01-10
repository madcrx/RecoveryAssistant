"""
RecoveryAssistant Desktop - Main Application Entry Point

A standalone Windows application for automated receivables collection.
Integrates with Microsoft Outlook and accounting software (Xero, QuickBooks).
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont

from app.gui.main_window import MainWindow
from app.models.database import DatabaseManager
from app.utils.config import ConfigManager
from app.utils.logger import setup_logging
from app.services.scheduler import BackgroundScheduler


def check_requirements():
    """Check system requirements before starting"""
    errors = []

    # Check Windows platform
    if sys.platform != 'win32':
        errors.append("RecoveryAssistant Desktop requires Windows OS")

    # Check Python version
    if sys.version_info < (3, 11):
        errors.append("Python 3.11 or higher is required")

    # Check for Outlook installation
    try:
        import win32com.client
        outlook = win32com.client.Dispatch("Outlook.Application")
        outlook = None  # Release COM object
    except Exception as e:
        errors.append(f"Microsoft Outlook not found or not accessible: {e}")

    return errors


def show_first_run_wizard(config_manager):
    """Show configuration wizard on first run"""
    from app.gui.setup_wizard import SetupWizard

    wizard = SetupWizard()
    if wizard.exec() == wizard.DialogCode.Accepted:
        # Save initial configuration
        config_data = wizard.get_configuration()
        config_manager.update_config(config_data)
        return True
    return False


def main():
    """Main application entry point"""

    # Initialize logging
    logger = setup_logging()
    logger.info("Starting RecoveryAssistant Desktop")

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("RecoveryAssistant")
    app.setOrganizationName("RecoveryAssistant")
    app.setApplicationVersion("1.0.0")

    # Set application style
    app.setStyle("Fusion")

    # Check system requirements
    errors = check_requirements()
    if errors:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("System Requirements Not Met")
        msg.setText("The following requirements are not met:")
        msg.setInformativeText("\n".join(errors))
        msg.exec()
        return 1

    # Show splash screen
    splash_pix = QPixmap(400, 300)
    splash_pix.fill(Qt.GlobalColor.white)
    splash = QSplashScreen(splash_pix)
    splash.setFont(QFont("Arial", 12))
    splash.show()

    def update_splash(message):
        splash.showMessage(
            message,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            Qt.GlobalColor.black
        )
        app.processEvents()

    try:
        # Initialize configuration manager
        update_splash("Loading configuration...")
        config_manager = ConfigManager()

        # Check if first run
        if not config_manager.is_configured():
            splash.close()
            if not show_first_run_wizard(config_manager):
                logger.info("User cancelled first-run setup")
                return 0
            splash.show()

        # Initialize database
        update_splash("Initializing database...")
        db_manager = DatabaseManager(config_manager.get_database_path())
        db_manager.init_database()

        # Initialize background scheduler
        update_splash("Starting background services...")
        scheduler = BackgroundScheduler(db_manager, config_manager)
        scheduler.start()

        # Create and show main window
        update_splash("Loading main window...")
        main_window = MainWindow(db_manager, config_manager, scheduler)

        # Close splash and show main window
        QTimer.singleShot(1000, splash.close)
        QTimer.singleShot(1000, main_window.show)

        logger.info("Application started successfully")

        # Run application event loop
        exit_code = app.exec()

        # Cleanup
        logger.info("Shutting down application")
        scheduler.stop()
        db_manager.close()

        return exit_code

    except Exception as e:
        logger.exception(f"Fatal error during startup: {e}")
        splash.close()

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("An error occurred while starting the application:")
        msg.setInformativeText(str(e))
        msg.setDetailedText(logger.get_last_error())
        msg.exec()

        return 1


if __name__ == "__main__":
    sys.exit(main())

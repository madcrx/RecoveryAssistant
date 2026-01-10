"""
Logging Setup

Configures application logging.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
import traceback


# Store last error for display
_last_error = None


class ErrorCapturingHandler(logging.Handler):
    """Handler that captures ERROR level messages"""

    def emit(self, record):
        global _last_error
        if record.levelno >= logging.ERROR:
            _last_error = self.format(record)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup application logging

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Root logger
    """

    # Create logs directory
    log_dir = Path.home() / "AppData" / "Roaming" / "RecoveryAssistant" / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log file path
    log_file = log_dir / f"recoveryassistant_{datetime.now().strftime('%Y%m%d')}.log"

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (rotating)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Error capturing handler
    error_handler = ErrorCapturingHandler()
    error_handler.setFormatter(file_format)
    logger.addHandler(error_handler)

    # Add get_last_error method to logger
    def get_last_error():
        """Get last error message with traceback"""
        if _last_error:
            return _last_error
        return traceback.format_exc()

    logger.get_last_error = get_last_error

    logger.info("Logging initialized")
    logger.info(f"Log file: {log_file}")

    return logger

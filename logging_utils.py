# logging_utils.py
# Version: 26.0.0
# Last modified: 2025-07-03
# Comprehensive logging system for the KYO QA Tool

from version import VERSION
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import error_tracker

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

SESSION_LOG_FILE = LOG_DIR / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_session.log"


class QtWidgetHandler(logging.Handler):
    """Simple handler that appends log messages to a text widget."""

    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        try:
            msg = self.format(record)
            # Try different methods to append text
            if hasattr(self.widget, "append"):
                self.widget.append(msg)
            elif hasattr(self.widget, "appendPlainText"):
                self.widget.appendPlainText(msg)
            elif hasattr(self.widget, "insertPlainText"):
                self.widget.insertPlainText(msg + "\n")
            elif hasattr(self.widget, "insert"):
                # For tkinter Text widget
                self.widget.config(state="normal")
                self.widget.insert("end", msg + "\n")
                self.widget.see("end")
                self.widget.config(state="disabled")
        except Exception:
            self.handleError(record)


def setup_logger(name: str, level=logging.INFO, log_widget=None, to_console=True) -> logging.Logger:
    """
    Set up a logger with file and optional console/widget output.
    
    Args:
        name: Logger name
        level: Logging level
        log_widget: Optional widget to send logs to
        to_console: Whether to log to console
        
    Returns:
        logging.Logger: Configured logger instance
    """
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(name)-20s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler
    try:
        file_handler = RotatingFileHandler(
            SESSION_LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create file handler: {e}")

    # Console handler
    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Widget handler
    if log_widget:
        widget_handler = QtWidgetHandler(log_widget)
        widget_handler.setLevel(level)
        widget_handler.setFormatter(formatter)
        logger.addHandler(widget_handler)

    # Sentry handler (if available)
    try:
        if error_tracker.init_error_tracker():
            sentry_handler = error_tracker.get_handler()
            if sentry_handler:
                sentry_handler.setLevel(logging.ERROR)
                logger.addHandler(sentry_handler)
    except Exception:
        pass  # Sentry is optional

    # Log startup message
    logger.info(f"Logger '{name}' initialized - KYO QA Tool v{VERSION}")
    
    return logger


def log_info(logger: logging.Logger, message: str):
    """Log an info message."""
    logger.info(message)


def log_warning(logger: logging.Logger, message: str):
    """Log a warning message."""
    logger.warning(message)


def log_error(logger: logging.Logger, message: str):
    """Log an error message."""
    logger.error(message)


def log_debug(logger: logging.Logger, message: str):
    """Log a debug message."""
    logger.debug(message)


def log_exception(logger: logging.Logger, message: str):
    """Log an exception with traceback."""
    logger.exception(message)


def create_session_summary():
    """Create a summary of the current session."""
    summary_file = LOG_DIR / f"{datetime.now():%Y%m%d}_session_summary.md"
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"# KYO QA Tool Session Summary\n\n")
            f.write(f"**Date:** {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            f.write(f"**Version:** {VERSION}\n\n")
            
            # Add session statistics if available
            if SESSION_LOG_FILE.exists():
                log_content = SESSION_LOG_FILE.read_text(encoding='utf-8')
                error_count = log_content.count('[ERROR')
                warning_count = log_content.count('[WARNING')
                info_count = log_content.count('[INFO')
                
                f.write(f"## Log Statistics\n\n")
                f.write(f"- Info messages: {info_count}\n")
                f.write(f"- Warning messages: {warning_count}\n")
                f.write(f"- Error messages: {error_count}\n\n")
                
                if error_count > 0:
                    f.write(f"## Errors Found\n\n")
                    for line in log_content.splitlines():
                        if '[ERROR' in line:
                            f.write(f"- {line}\n")
                    f.write("\n")
        
        return summary_file
    except Exception as e:
        print(f"Could not create session summary: {e}")
        return None


def cleanup_old_logs(max_age_days=30):
    """
    Clean up old log files.
    
    Args:
        max_age_days: Maximum age in days for log files to keep
        
    Returns:
        int: Number of files deleted
    """
    if not LOG_DIR.exists():
        return 0
    
    import time
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    deleted_count = 0
    
    try:
        for log_file in LOG_DIR.glob("*.log*"):
            if log_file.is_file():
                file_age = current_time - log_file.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        log_file.unlink()
                        deleted_count += 1
                    except Exception:
                        pass  # Ignore errors when deleting old files
        
        return deleted_count
    except Exception:
        return 0


def get_log_level_from_string(level_str: str) -> int:
    """
    Convert string log level to logging constant.
    
    Args:
        level_str: String representation of log level
        
    Returns:
        int: Logging level constant
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    return level_map.get(level_str.upper(), logging.INFO)


def configure_root_logger(level=logging.INFO):
    """
    Configure the root logger with basic settings.
    
    Args:
        level: Logging level for root logger
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            RotatingFileHandler(
                SESSION_LOG_FILE,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
                encoding='utf-8'
            )
        ]
    )


def log_system_info(logger: logging.Logger):
    """Log system information for debugging purposes."""
    import platform
    
    logger.info("=== System Information ===")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Architecture: {platform.architecture()[0]}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info(f"Working Directory: {Path.cwd()}")
    logger.info(f"KYO QA Tool Version: {VERSION}")
    logger.info("=== End System Information ===")


class ContextFilter(logging.Filter):
    """Add context information to log records."""
    
    def __init__(self, context_data=None):
        super().__init__()
        self.context_data = context_data or {}
    
    def filter(self, record):
        for key, value in self.context_data.items():
            setattr(record, key, value)
        return True


def add_context_to_logger(logger: logging.Logger, **context):
    """
    Add context information to all log messages from a logger.
    
    Args:
        logger: Logger to add context to
        **context: Key-value pairs to add as context
    """
    context_filter = ContextFilter(context)
    logger.addFilter(context_filter)


# Configure root logger on import
configure_root_logger()
# KYO QA ServiceNow Logging Utilities - FINAL VERSION (Corrected)
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from version import VERSION


class QtWidgetHandler(logging.Handler):
    """Handler to append log messages to a QTextEdit widget."""

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        try:
            from PySide6 import QtCore
            self._invoker = lambda msg: QtCore.QMetaObject.invokeMethod(
                self.text_edit,
                "append",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, msg),
            )
        except Exception:
            # Fallback: direct call if PySide6 not available
            self._invoker = lambda msg: self.text_edit.append(msg)

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self._invoker(msg)

# Define Log Directory correctly relative to the project folder
LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

SESSION_LOG_FILE = LOG_DIR / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_session.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"

def setup_logger(name: str, level=logging.INFO, log_widget=None) -> logging.Logger:
    """Sets up loggers with handlers for session, error, console, and optional GUI logging."""
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(name)-20s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.DEBUG)

        # Handler for the detailed session log
        session_handler = RotatingFileHandler(SESSION_LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
        session_handler.setFormatter(formatter)
        session_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(session_handler)

        # Handler for the persistent error log
        error_handler = RotatingFileHandler(ERROR_LOG_FILE, maxBytes=2*1024*1024, backupCount=2, encoding="utf-8")
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Handler for console output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        root_logger.addHandler(console_handler)

        root_logger.info(f"Logging initialized. Session: {SESSION_LOG_FILE} | Errors: {ERROR_LOG_FILE}")

    if log_widget:
        # Avoid adding duplicate GUI handlers for the same widget
        if not any(isinstance(h, QtWidgetHandler) and getattr(h, "text_edit", None) is log_widget for h in root_logger.handlers):
            gui_handler = QtWidgetHandler(log_widget)
            gui_handler.setFormatter(formatter)
            gui_handler.setLevel(level)
            root_logger.addHandler(gui_handler)

    return logging.getLogger(name)

# --- FIX: Adding the missing helper functions back into the file ---

def log_info(logger: logging.Logger, message: str) -> None:
    """A consistent wrapper for logging info messages."""
    logger.info(message)

def log_error(logger: logging.Logger, message: str) -> None:
    """A consistent wrapper for logging error messages."""
    logger.error(message)

def log_warning(logger: logging.Logger, message: str) -> None:
    """A consistent wrapper for logging warning messages."""
    logger.warning(message)

def log_exception(logger: logging.Logger, message: str) -> None:
    """A consistent wrapper for logging exceptions with tracebacks."""
    logger.exception(message)

def create_success_log(message, output_file=None):
    """Creates a markdown summary log for successful runs."""
    if output_file is None:
        output_file = LOG_DIR / f"{datetime.now():%Y%m%d}_SUCCESSlog.md"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# KYO QA Tool Success Log - {VERSION}\n\n")
            f.write(f"**Date:** {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
            f.write("## Summary\n\n")
            f.write(message + "\n\n")
        return str(output_file)
    except Exception as e:
        log_error(setup_logger("log_creation"), f"Failed to create success log: {e}")
        return None

def create_failure_log(message, error_details, output_file=None):
    """Creates a markdown summary log for failed runs."""
    if output_file is None:
        output_file = LOG_DIR / f"{datetime.now():%Y%m%d}_FAILlog.md"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# KYO QA Tool Failure Log - {VERSION}\n\n")
            f.write(f"**Date:** {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
            f.write("## Error Summary\n\n")
            f.write(message + "\n\n")
            f.write("## Technical Details\n\n")
            f.write("```\n")
            f.write(str(error_details))
            f.write("\n```\n")
        return str(output_file)
    except Exception as e:
        log_error(setup_logger("log_creation"), f"Failed to create failure log: {e}")
        return None
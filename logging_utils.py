# KYO QA ServiceNow Logging Utilities - REPAIRED
from version import VERSION
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOG_DIR = Path.cwd() / "logs"
LOG_DIR.mkdir(exist_ok=True)

SESSION_LOG_FILE = LOG_DIR / f"{datetime.now():%Y-%m-%d_%H-%M-%S}_session.log"


class QtWidgetHandler(logging.Handler):
    """Simple handler that appends log messages to a text widget."""

    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):  # pragma: no cover - simple UI helper
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
                self.widget.insert("end", msg + "\n")
                self.widget.see("end")
        except Exception:
            self.handleError(record)


def setup_logger(name: str, level=logging.INFO, log_widget=None) -> logging.Logger:
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(name)-20s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(level)
        file_handler = RotatingFileHandler(
            SESSION_LOG_FILE,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        root_logger.info(f"Logging initialized for session. Log file: {SESSION_LOG_FILE}")

    logger = logging.getLogger(name)
    
    if log_widget is not None:
        # Check if a widget handler already exists for this logger
        widget_handlers = [h for h in logger.handlers if isinstance(h, QtWidgetHandler)]
        if not widget_handlers:
            widget_handler = QtWidgetHandler(log_widget)
            widget_handler.setFormatter(formatter)
            logger.addHandler(widget_handler)
    
    return logger


def log_info(logger: logging.Logger, message: str) -> None:
    logger.info(message)


def log_error(logger: logging.Logger, message: str) -> None:
    logger.error(message)


def log_warning(logger: logging.Logger, message: str) -> None:
    logger.warning(message)


def log_exception(logger: logging.Logger, message: str) -> None:
    logger.exception(message)


def create_success_log(message, output_file=None):
    if output_file is None:
        output_file = LOG_DIR / f"{datetime.now():%Y%m%d}_SUCCESSlog.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# KYO QA Tool Success Log - {VERSION}\n\n")
        f.write(f"**Date:** {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
        f.write("## Summary\n\n")
        f.write(message + "\n\n")
    return str(output_file)


def create_failure_log(message, error_details, output_file=None):
    if output_file is None:
        output_file = LOG_DIR / f"{datetime.now():%Y%m%d}_FAILlog.md"
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
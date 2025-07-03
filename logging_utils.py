# KYO QA ServiceNow Logging Utilities - REPAIRED
from version import VERSION
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import error_tracker

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


def setup_logger(name: str, level=logging.INFO, log_widget=None, to_console=False) -> logging.Logger:
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] [%(name)-20s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
  

# error_tracker.py
# Version: 26.0.0
# Last modified: 2025-07-03
"""Simple error tracking and exception hook setup."""

import logging
import os
import sys
from pathlib import Path

from logging_utils import setup_logger, log_exception

_logger = setup_logger("error_tracker")

ERROR_FILE = Path("error_log.txt")


def _write_error_file(exc_type, exc, tb):
    """Append exception details to error_log.txt with stack trace."""
    with ERROR_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{exc_type.__name__}: {exc}\n")
        import traceback
        traceback.print_tb(tb, file=f)
        f.write("\n")


def exception_hook(exc_type, exc, tb):
    """Global exception hook that logs and writes errors."""
    log_exception(_logger, "Unhandled exception")
    _write_error_file(exc_type, exc, tb)
    if _prev_hook:
        _prev_hook(exc_type, exc, tb)

_prev_hook = sys.excepthook


def install():
    """Install global exception hook for error tracking."""
    sys.excepthook = exception_hook



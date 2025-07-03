import sys
import importlib

import error_tracker


def test_install_sets_hook():
    importlib.reload(error_tracker)
    original = sys.excepthook
    error_tracker.install()
    try:
        assert sys.excepthook == error_tracker.exception_hook
    finally:
        sys.excepthook = original


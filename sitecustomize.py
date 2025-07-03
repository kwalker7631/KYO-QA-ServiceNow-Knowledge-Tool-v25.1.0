"""Site customizations for test runs."""
import sys
import importlib

try:
    import openpyxl  # noqa: F401
except Exception:
    try:
        from tests.openpyxl_stub import ensure_openpyxl_stub
    except Exception:
        def ensure_openpyxl_stub():
            return
    ensure_openpyxl_stub()

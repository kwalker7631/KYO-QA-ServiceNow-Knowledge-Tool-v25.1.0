import sys

from tests.openpyxl_stub import ensure_openpyxl_stub


def test_ensure_openpyxl_stub():
    sys.modules.pop('openpyxl', None)
    sys.modules.pop('openpyxl.styles', None)
    sys.modules.pop('openpyxl.utils', None)
    sys.modules.pop('openpyxl.utils.exceptions', None)
    sys.modules.pop('openpyxl.formatting.rule', None)
    ensure_openpyxl_stub()
    import openpyxl
    assert hasattr(openpyxl, 'load_workbook')
    assert 'openpyxl.styles' in sys.modules
    assert 'openpyxl.utils' in sys.modules

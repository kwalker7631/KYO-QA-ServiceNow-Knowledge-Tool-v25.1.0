import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import types
if 'openpyxl' not in sys.modules:
    openpyxl = types.ModuleType('openpyxl')
    styles = types.ModuleType('styles')
    class Dummy:
        def __init__(self, *a, **k):
            pass

    styles.PatternFill = Dummy
    styles.Alignment = Dummy
    styles.Font = Dummy
    openpyxl.styles = styles
    openpyxl.Workbook = Dummy
    openpyxl.load_workbook = lambda *a, **k: Dummy()
    formatting = types.ModuleType('formatting')
    rule_mod = types.ModuleType('rule')
    rule_mod.FormulaRule = Dummy
    formatting.rule = rule_mod
    openpyxl.formatting = formatting
    utils = types.ModuleType('utils')
    utils.get_column_letter = lambda x: x
    openpyxl.utils = utils
    sys.modules['openpyxl'] = openpyxl
    sys.modules['openpyxl.styles'] = styles
    sys.modules['openpyxl.formatting'] = formatting
    sys.modules['openpyxl.formatting.rule'] = rule
    sys.modules['openpyxl.utils'] = utils

import kyo_qa_tool_app


def test_QAApp_alias():
    assert issubclass(kyo_qa_tool_app.QAApp, kyo_qa_tool_app.KyoQAToolApp)

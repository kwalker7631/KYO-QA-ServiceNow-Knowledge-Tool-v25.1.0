import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import types
if 'openpyxl' not in sys.modules:
    openpyxl = types.ModuleType('openpyxl')
    styles = types.ModuleType('styles')
    styles.PatternFill = object
    styles.Alignment = object
    openpyxl.styles = styles
    utils = types.ModuleType('utils')
    utils.get_column_letter = lambda x: x
    openpyxl.utils = utils
    sys.modules['openpyxl'] = openpyxl
    sys.modules['openpyxl.styles'] = styles
    sys.modules['openpyxl.utils'] = utils

import kyo_qa_tool_app


def test_QAApp_alias():
    assert issubclass(kyo_qa_tool_app.QAApp, kyo_qa_tool_app.KyoQAToolApp)

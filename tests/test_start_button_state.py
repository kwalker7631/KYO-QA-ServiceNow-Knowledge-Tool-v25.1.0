import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub openpyxl to satisfy imports if missing
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

if 'fitz' not in sys.modules:
    sys.modules['fitz'] = types.ModuleType('fitz')

import kyo_qa_tool_app

class DummyVar:
    def __init__(self, val=""):
        self.val = val
    def get(self):
        return self.val
    def set(self, v):
        self.val = v

class DummyButton:
    def __init__(self):
        self.state = None
    def config(self, state=None):
        self.state = state


def test_update_start_button_state_enables_when_inputs_ready():
    dummy = types.SimpleNamespace(
        selected_excel=DummyVar(),
        selected_folder=DummyVar(),
        selected_files_list=[],
        process_btn=DummyButton(),
    )

    kyo_qa_tool_app.QAApp.update_start_button_state(dummy)
    assert dummy.process_btn.state == kyo_qa_tool_app.tk.DISABLED

    dummy.selected_excel.set("base.xlsx")
    dummy.selected_folder.set("/data")
    kyo_qa_tool_app.QAApp.update_start_button_state(dummy)
    assert dummy.process_btn.state == kyo_qa_tool_app.tk.NORMAL

    dummy.selected_folder.set("")
    dummy.selected_files_list = ["a.pdf"]
    kyo_qa_tool_app.QAApp.update_start_button_state(dummy)
    assert dummy.process_btn.state == kyo_qa_tool_app.tk.NORMAL


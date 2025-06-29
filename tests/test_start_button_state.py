import sys
import types
from pathlib import Path
import importlib
import tkinter as tk

sys.path.append(str(Path(__file__).resolve().parents[1]))


class DummyVar:
    def __init__(self, value=""):
        self._value = value
        self._callbacks = []

    def get(self):
        return self._value

    def set(self, value):
        self._value = value
        for cb in self._callbacks:
            cb()

    def trace_add(self, _mode, callback):
        self._callbacks.append(lambda: callback(None, None, None))


class DummyButton:
    def __init__(self):
        self.state = tk.DISABLED

    def config(self, **kwargs):
        self.state = kwargs.get("state", self.state)


def create_dummy_app():
    for mod in ['openpyxl', 'fitz']:
        if mod not in sys.modules:
            sys.modules[mod] = types.ModuleType(mod)
    if 'openpyxl.styles' not in sys.modules:
        styles = types.ModuleType('styles')
        styles.PatternFill = object
        styles.Alignment = object
        sys.modules['openpyxl.styles'] = styles
    if 'openpyxl.utils' not in sys.modules:
        utils = types.ModuleType('utils')
        utils.get_column_letter = lambda x: x
        sys.modules['openpyxl.utils'] = utils

    mod = importlib.reload(importlib.import_module('kyo_qa_tool_app'))

    dummy = types.SimpleNamespace()
    dummy.selected_excel = DummyVar()
    dummy.selected_folder = DummyVar()
    dummy.selected_files_list = []
    dummy.process_btn = DummyButton()
    dummy.update_start_button_state = mod.QAApp.update_start_button_state.__get__(dummy, type(dummy))
    dummy.selected_folder.trace_add("write", lambda *a: dummy.update_start_button_state())
    dummy.selected_excel.trace_add("write", lambda *a: dummy.update_start_button_state())
    return dummy


def test_button_state_toggles_with_inputs():
    app = create_dummy_app()

    # initially disabled
    app.update_start_button_state()
    assert app.process_btn.state == tk.DISABLED

    # select excel only
    app.selected_excel.set("base.xlsx")
    assert app.process_btn.state == tk.DISABLED

    # select folder in addition -> enabled
    app.selected_folder.set("/data")
    assert app.process_btn.state == tk.NORMAL

    # clear excel -> disabled again
    app.selected_excel.set("")
    assert app.process_btn.state == tk.DISABLED

    # set excel and use pdf list instead of folder
    app.selected_excel.set("base.xlsx")
    app.selected_folder.set("")
    app.selected_files_list = ["a.pdf"]
    app.update_start_button_state()
    assert app.process_btn.state == tk.NORMAL

    # clear file list -> disabled
    app.selected_files_list = []
    app.update_start_button_state()
    assert app.process_btn.state == tk.DISABLED

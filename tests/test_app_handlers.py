import sys
import unittest.mock as mock

sys.modules.setdefault("openpyxl", mock.MagicMock())
sys.modules.setdefault("openpyxl.styles", mock.MagicMock())
sys.modules.setdefault("openpyxl.utils", mock.MagicMock())
sys.modules.setdefault("fitz", mock.MagicMock())

import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import tkinter as tk
import types

tk.ttk = types.SimpleNamespace(Style=lambda *a, **k: mock.MagicMock())

class DummyVar:
    def __init__(self, value=None):
        self.value = value
    def get(self):
        return self.value
    def set(self, value):
        self.value = value

class DummyTk:
    def __init__(self, *a, **k):
        self._w = '.'
        self.children = {}
    def withdraw(self):
        pass
    def destroy(self):
        pass
    def after(self, *a, **k):
        pass


def test_toggle_pause(monkeypatch):
    monkeypatch.setattr(tk, 'Tk', DummyTk)
    monkeypatch.setattr(tk, 'DoubleVar', lambda *a, **k: DummyVar())
    monkeypatch.setattr(tk, 'StringVar', lambda *a, **k: DummyVar())
    monkeypatch.setattr(tk, 'IntVar', lambda *a, **k: DummyVar())
    monkeypatch.setattr('kyo_qa_tool_app.KyoQAToolApp._setup_window_styles', lambda self: None)
    monkeypatch.setattr('kyo_qa_tool_app.KyoQAToolApp._create_widgets', lambda self: None)
    from kyo_qa_tool_app import KyoQAToolApp
    app = KyoQAToolApp()
    app.pause_btn = mock.MagicMock()
    app.pause_btn.config = lambda *a, **k: None
    app.is_processing = True
    app.toggle_pause()
    assert app.is_paused
    assert app.pause_event.is_set()
    app.toggle_pause()
    assert not app.is_paused
    assert not app.pause_event.is_set()
    app.destroy()


def test_browse_excel(monkeypatch):
    monkeypatch.setattr(tk, 'Tk', DummyTk)
    monkeypatch.setattr(tk, 'DoubleVar', lambda *a, **k: DummyVar())
    monkeypatch.setattr(tk, 'StringVar', lambda *a, **k: DummyVar())
    monkeypatch.setattr(tk, 'IntVar', lambda *a, **k: DummyVar())
    monkeypatch.setattr('kyo_qa_tool_app.KyoQAToolApp._setup_window_styles', lambda self: None)
    monkeypatch.setattr('kyo_qa_tool_app.KyoQAToolApp._create_widgets', lambda self: None)
    monkeypatch.setattr('tkinter.filedialog.askopenfilename', lambda *a, **k: 'file.xlsx')
    from kyo_qa_tool_app import KyoQAToolApp
    app = KyoQAToolApp()
    app.browse_excel()
    assert app.selected_excel.get() == 'file.xlsx'
    app.destroy()


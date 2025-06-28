import sys
import types
from pathlib import Path

# Stub heavy modules if missing
for mod in ('pandas', 'fitz'):
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

import processing_engine
from config import HEADER_MAPPING

# ruff: noqa: E402


class DummyEvent:
    def is_set(self):
        return False


class DummySeries(list):
    def __eq__(self, other):
        return DummySeries([x == other for x in self])

    def __getitem__(self, item):
        if isinstance(item, list):
            return DummySeries([x for x, flag in zip(self, item) if flag])
        return super().__getitem__(item)

    def tolist(self):
        return list(self)


class DummyDataFrame:
    def __init__(self, rows):
        self.rows = rows
        self.columns = list(rows[0].keys())
        self.index = DummySeries(list(range(len(rows))))
        self.at = _AtAccessor(self)

    def __getitem__(self, key):
        return DummySeries([row.get(key) for row in self.rows])

    def to_excel(self, *args, **kwargs):
        pass


class _AtAccessor:
    def __init__(self, df):
        self.df = df

    def __getitem__(self, key):
        row, col = key
        return self.df.rows[row][col]

    def __setitem__(self, key, value):
        row, col = key
        self.df.rows[row][col] = value


def make_dataframe(filename):
    cols = list(HEADER_MAPPING.values())
    row = {col: '' for col in cols}
    row['Description'] = filename
    return DummyDataFrame([row])


def test_ocr_callback_invoked(monkeypatch):
    df = make_dataframe('file.pdf')
    monkeypatch.setattr(processing_engine.pd, 'read_excel', lambda *a, **k: df, raising=False)
    monkeypatch.setattr(processing_engine.pd, 'isna', lambda x: x == '' or x is None, raising=False)
    monkeypatch.setattr(processing_engine, 'is_file_locked', lambda p: False)
    monkeypatch.setattr(
        processing_engine,
        'extract_text_from_pdf',
        lambda p, cb=None: (cb() if cb else None) or 'text'
    )
    monkeypatch.setattr(processing_engine, '_is_ocr_needed', lambda p: True)
    monkeypatch.setattr(processing_engine, 'ai_extract', lambda text, path: {})

    ocr_calls = []
    processing_engine._main_processing_loop([Path('file.pdf')], 'kb.xlsx', lambda x: None, lambda a,b: None, lambda: ocr_calls.append(1), lambda: None, DummyEvent())
    assert len(ocr_calls) == 1


def test_needs_review_callback_invoked(monkeypatch):
    df = make_dataframe('file.pdf')
    monkeypatch.setattr(processing_engine.pd, 'read_excel', lambda *a, **k: df, raising=False)
    monkeypatch.setattr(processing_engine.pd, 'isna', lambda x: x == '' or x is None, raising=False)
    monkeypatch.setattr(processing_engine, 'is_file_locked', lambda p: False)
    monkeypatch.setattr(
        processing_engine,
        'extract_text_from_pdf',
        lambda p, cb=None: 'text'
    )
    monkeypatch.setattr(processing_engine, '_is_ocr_needed', lambda p: False)
    monkeypatch.setattr(processing_engine, 'ai_extract', lambda text, path: {'needs_review': True})

    review_calls = []
    processing_engine._main_processing_loop([Path('file.pdf')], 'kb.xlsx', lambda x: None, lambda a,b: None, lambda: None, lambda: review_calls.append(1), DummyEvent())
    assert len(review_calls) == 1

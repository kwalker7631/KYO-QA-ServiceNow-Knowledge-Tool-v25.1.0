import sys
import types
from pathlib import Path
import threading

# Ensure repo root is on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import processing_engine

class DummyDF:
    def __init__(self, rows):
        self.rows = rows
        self.columns = list(rows[0].keys())
        self.at = _DummyAt(rows)

    def __getitem__(self, key):
        return _Series([row[key] for row in self.rows])

    @property
    def index(self):
        return _DummyIndex(len(self.rows))

    def to_excel(self, *a, **k):
        pass

class _DummyIndex:
    def __init__(self, length):
        self.length = length

    def __getitem__(self, cond):
        return _IndexResult([i for i, c in enumerate(cond) if c])

    def tolist(self):
        return list(range(self.length))

class _DummyAt:
    def __init__(self, rows):
        self.rows = rows

    def __getitem__(self, key):
        r, c = key
        return self.rows[r].get(c)

    def __setitem__(self, key, value):
        r, c = key
        self.rows[r][c] = value


class _Series(list):
    def __eq__(self, other):
        return [x == other for x in self]


class _IndexResult(list):
    def tolist(self):
        return list(self)


def setup_pandas_stub(monkeypatch, df):
    fake_pd = types.ModuleType('pandas')
    fake_pd.read_excel = lambda *a, **k: df
    fake_pd.isna = lambda v: v is None or v == ''
    monkeypatch.setitem(sys.modules, 'pandas', fake_pd)
    monkeypatch.setattr(processing_engine, 'pd', fake_pd, raising=False)


def test_callbacks_success_and_failure(monkeypatch, tmp_path):
    p1 = tmp_path / "a.pdf"
    p2 = tmp_path / "b.pdf"
    p1.write_text("1")
    p2.write_text("2")
    rows = [
        {"Description": "a.pdf", "Author": None},
        {"Description": "b.pdf", "Author": None},
    ]
    df = DummyDF(rows)
    setup_pandas_stub(monkeypatch, df)
    monkeypatch.setattr(processing_engine, 'is_file_locked', lambda p: False)
    monkeypatch.setattr(processing_engine, '_is_ocr_needed', lambda p: p == p1)
    monkeypatch.setattr(
        processing_engine, 'extract_text_from_pdf', lambda p: "text" if p == p1 else ""
    )
    monkeypatch.setattr(processing_engine, 'ai_extract', lambda t, p: {})

    calls = {"s": 0, "f": 0, "r": 0, "o": 0}
    def inc(key):
        def _():
            calls[key] += 1
        return _

    processing_engine._main_processing_loop(
        [p1, p2],
        str(tmp_path / "kb.xlsx"),
        lambda *a: None,
        lambda *a: None,
        inc("s"),
        inc("f"),
        inc("r"),
        inc("o"),
        threading.Event(),
    )

    assert calls == {"s": 1, "f": 1, "r": 0, "o": 1}


def test_callbacks_needs_review(monkeypatch, tmp_path):
    p1 = tmp_path / "c.pdf"
    p1.write_text("c")
    rows = [{"Description": "c.pdf", "Author": None}]
    df = DummyDF(rows)
    setup_pandas_stub(monkeypatch, df)
    monkeypatch.setattr(processing_engine, 'is_file_locked', lambda p: False)
    monkeypatch.setattr(processing_engine, '_is_ocr_needed', lambda p: False)
    monkeypatch.setattr(processing_engine, 'extract_text_from_pdf', lambda p: "text")
    monkeypatch.setattr(processing_engine, 'ai_extract', lambda t, p: {"needs_review": True})

    calls = {"s": 0, "f": 0, "r": 0, "o": 0}
    def inc(key):
        def _():
            calls[key] += 1
        return _

    processing_engine._main_processing_loop(
        [p1],
        str(tmp_path / "kb.xlsx"),
        lambda *a: None,
        lambda *a: None,
        inc("s"),
        inc("f"),
        inc("r"),
        inc("o"),
        threading.Event(),
    )

    assert calls == {"s": 1, "f": 0, "r": 1, "o": 0}

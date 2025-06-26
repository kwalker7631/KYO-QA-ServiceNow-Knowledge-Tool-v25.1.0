import sys
import importlib
from types import SimpleNamespace, ModuleType
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Ensure stub modules for optional deps
sys.modules.setdefault('fitz', ModuleType('fitz'))
if 'dateutil' not in sys.modules:
    sys.modules['dateutil'] = ModuleType('dateutil')
if 'dateutil.relativedelta' not in sys.modules:
    rd = ModuleType('dateutil.relativedelta')
    class _RD:
        def __init__(self, **kw):
            pass
    rd.relativedelta = _RD
    sys.modules['dateutil.relativedelta'] = rd


class DummySeries(list):
    def __eq__(self, other):
        return [x == other for x in self]


class DummyIndex(list):
    def __getitem__(self, item):
        if isinstance(item, list):
            return DummyIndex([v for v, flag in zip(self, item) if flag])
        return super().__getitem__(item)

    def tolist(self):
        return list(self)


class DummyDF:
    def __init__(self):
        self.data = {'Description': ['file.pdf']}
        self.columns = ['Description']
        self.index = DummyIndex([0])

    def __getitem__(self, key):
        return DummySeries(self.data[key])

    @property
    def at(self):
        df = self
        class _Accessor:
            def __getitem__(self, idx):
                row, col = idx
                return df.data.get(col, [None])[row]
            def __setitem__(self, idx, value):
                row, col = idx
                df.data.setdefault(col, [None] * len(df.index))
                df.data[col][row] = value
        return _Accessor()

    def to_excel(self, *a, **k):
        pass


def test_success_log_called(monkeypatch):
    pandas_stub = ModuleType('pandas')
    pandas_stub.DataFrame = DummyDF
    pandas_stub.isna = lambda x: x is None
    monkeypatch.setitem(sys.modules, 'pandas', pandas_stub)

    processing_engine = importlib.reload(importlib.import_module('processing_engine'))

    dummy_df = DummyDF()
    monkeypatch.setattr(processing_engine.pd, 'read_excel', lambda *a, **k: dummy_df, raising=False)
    monkeypatch.setattr(processing_engine.pd, 'isna', lambda x: x is None, raising=False)
    monkeypatch.setattr(processing_engine.pd.DataFrame, 'to_excel', lambda self, *a, **k: None, raising=False)
    monkeypatch.setattr(processing_engine, 'is_file_locked', lambda p: False)
    monkeypatch.setattr(processing_engine, 'extract_text_from_pdf', lambda p: 'txt')
    monkeypatch.setattr(processing_engine, 'ai_extract', lambda text, path: {})
    monkeypatch.setattr(processing_engine, '_is_ocr_needed', lambda p: False)

    captured = {}
    monkeypatch.setattr(processing_engine, 'create_success_log', lambda msg: captured.setdefault('success', msg))
    monkeypatch.setattr(processing_engine, 'create_failure_log', lambda *a, **k: captured.setdefault('failure', True))

    cancel = SimpleNamespace(is_set=lambda: False)
    processing_engine._main_processing_loop([Path('file.pdf')], 'kb.xlsx', lambda x: None, lambda *a: None, cancel)

    assert '1 record' in captured.get('success', '')
    assert 'failure' not in captured


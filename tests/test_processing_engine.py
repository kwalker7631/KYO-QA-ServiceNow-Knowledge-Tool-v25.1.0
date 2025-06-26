import sys
from pathlib import Path
import types

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

for mod in ('pandas', 'fitz'):
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

if 'dateutil' not in sys.modules:
    dateutil = types.ModuleType('dateutil')
    sys.modules['dateutil'] = dateutil
if 'dateutil.relativedelta' not in sys.modules:
    rd = types.ModuleType('dateutil.relativedelta')
    class _RD:
        def __init__(self, **kw):
            pass
    rd.relativedelta = _RD
    sys.modules['dateutil.relativedelta'] = rd

import processing_engine
from config import HEADER_MAPPING


def make_dummy_df():
    row = {h: "" for h in HEADER_MAPPING.values()}
    row['Description'] = 'test.pdf'
    class DummyDF:
        def __init__(self, data):
            self._data = data
            self.columns = list(data.keys())
            self._index = [0]

        def __getitem__(self, key):
            class SeriesLike(list):
                def __eq__(self, other):
                    return [x == other for x in self]
            return SeriesLike(self._data[key])

        @property
        def index(self):
            class DummyIndex(list):
                def __getitem__(self, mask):
                    if isinstance(mask, list):
                        return DummyIndex([x for x, m in zip(self, mask) if m])
                    return list.__getitem__(self, mask)

                def tolist(self):
                    return list(self)

            return DummyIndex(self._index)

        @property
        def at(self):
            class AtAccessor:
                def __init__(self, parent):
                    self.parent = parent

                def __getitem__(self, key):
                    row, col = key
                    return self.parent._data[col][row]

                def __setitem__(self, key, value):
                    row, col = key
                    self.parent._data[col][row] = value

            return AtAccessor(self)

        def to_excel(self, *a, **k):
            pass

    return DummyDF({k: [v] for k, v in row.items()})


def test_main_loop_calls_ocr_callback(monkeypatch):
    called = {'ocr': False}
    dummy_df = make_dummy_df()
    dummy_pd = types.SimpleNamespace(
        read_excel=lambda *a, **k: make_dummy_df(),
        DataFrame=dummy_df.__class__,
        isna=lambda x: x in (None, ""),
    )
    monkeypatch.setattr(processing_engine, 'pd', dummy_pd)
    monkeypatch.setattr(processing_engine, '_is_ocr_needed', lambda x: True)
    monkeypatch.setattr(processing_engine, 'extract_text_from_pdf', lambda x: 'text')
    monkeypatch.setattr(processing_engine, 'ai_extract', lambda t, f: {'subject': 's', 'models': 'm'})

    import threading
    event = threading.Event()

    def ocr_cb():
        called['ocr'] = True

    processing_engine._main_processing_loop([Path('test.pdf')], 'kb.xlsx', lambda m: None, lambda a,b: None, ocr_cb, event)

    assert called['ocr']

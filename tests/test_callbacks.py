import sys
import types
from pathlib import Path
import threading

# Ensure repository root is on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub external dependencies used by processing_engine
for mod in ("fitz",):
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)

if "dateutil" not in sys.modules:
    dateutil = types.ModuleType("dateutil")
    sys.modules["dateutil"] = dateutil
if "dateutil.relativedelta" not in sys.modules:
    rd = types.ModuleType("dateutil.relativedelta")
    class _RD:
        def __init__(self, **kw):
            pass
    rd.relativedelta = _RD
    sys.modules["dateutil.relativedelta"] = rd


class FakeColumn(list):
    def __eq__(self, other):
        return [v == other for v in self]


class FakeIndex(list):
    def __getitem__(self, item):
        if isinstance(item, list):
            return FakeIndex([idx for idx, flag in zip(self, item) if flag])
        return super().__getitem__(item)

    def tolist(self):
        return list(self)


class FakeAtAccessor:
    def __init__(self, df):
        self.df = df

    def __getitem__(self, key):
        row, col = key
        return self.df._data[col][row]

    def __setitem__(self, key, value):
        row, col = key
        self.df._data[col][row] = value


class FakeDF:
    def __init__(self):
        self._data = {"Description": ["file1.pdf"], "Author": [""]}
        self.columns = list(self._data.keys())
        self._index = FakeIndex([0])
        self.at = FakeAtAccessor(self)

    def __getitem__(self, key):
        return FakeColumn(self._data[key])

    @property
    def index(self):
        return self._index

    def to_excel(self, *a, **k):
        pass


def isna(value):
    return value in (None, "")

pd_stub_module = types.ModuleType("pandas")
pd_stub_module.read_excel = lambda *a, **k: FakeDF()
pd_stub_module.isna = isna
sys.modules.setdefault("pandas", pd_stub_module)

import processing_engine


def test_main_loop_triggers_callbacks(monkeypatch):
    callbacks = {"success": 0, "fail": 0, "review": 0, "ocr": 0}

    pd_stub = types.SimpleNamespace(read_excel=lambda *a, **k: FakeDF(), isna=isna)
    monkeypatch.setattr(processing_engine, "pd", pd_stub)
    monkeypatch.setattr(processing_engine, "_is_ocr_needed", lambda p: True)
    monkeypatch.setattr(processing_engine, "extract_text_from_pdf", lambda p: "text")
    monkeypatch.setattr(processing_engine, "ai_extract", lambda t, p: {"needs_review": True})
    monkeypatch.setattr(processing_engine, "map_to_servicenow_format", lambda d, n: {"Author": "A", "Description": n})

    def success():
        callbacks["success"] += 1

    def fail():
        callbacks["fail"] += 1

    def review():
        callbacks["review"] += 1

    def ocr():
        callbacks["ocr"] += 1

    processing_engine._main_processing_loop(
        [Path("file1.pdf")],
        "dummy.xlsx",
        lambda x: None,
        lambda *a: None,
        threading.Event(),
        success_cb=success,
        failure_cb=fail,
        needs_review_cb=review,
        ocr_cb=ocr,
    )

    assert callbacks == {"success": 1, "fail": 0, "review": 1, "ocr": 1}

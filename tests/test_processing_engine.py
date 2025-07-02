import queue
import sys
import types

# ruff: noqa: E402

# Stub dependencies not available in the test environment
fake_ocr_utils = types.ModuleType("ocr_utils")
fake_ocr_utils.extract_text_from_pdf = lambda p: ""
fake_ocr_utils._is_ocr_needed = lambda p: False
sys.modules["ocr_utils"] = fake_ocr_utils

fake_openpyxl = types.ModuleType("openpyxl")
fake_openpyxl.load_workbook = lambda *a, **k: None

styles_mod = types.ModuleType("openpyxl.styles")
styles_mod.PatternFill = lambda **kw: None
sys.modules["openpyxl.styles"] = styles_mod

utils_ex = types.ModuleType("openpyxl.utils.exceptions")
utils_ex.InvalidFileException = Exception
sys.modules["openpyxl.utils.exceptions"] = utils_ex

utils_mod = types.ModuleType("openpyxl.utils")
utils_mod.exceptions = utils_ex
utils_mod.get_column_letter = lambda x: "A"
sys.modules["openpyxl.utils"] = utils_mod

fake_openpyxl.styles = styles_mod
fake_openpyxl.utils = utils_mod
sys.modules["openpyxl"] = fake_openpyxl

import processing_engine


def test_process_single_pdf_ocr_failed(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("dummy")
    processing_engine.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(processing_engine, "PDF_TXT_DIR", tmp_path)
    processing_engine.PDF_TXT_DIR.mkdir(exist_ok=True)
    monkeypatch.setattr(processing_engine, "extract_text_from_pdf", lambda p: "")
    monkeypatch.setattr(processing_engine, "_is_ocr_needed", lambda p: True)
    q = queue.Queue()
    result = processing_engine.process_single_pdf(pdf, q)
    while not q.empty():
        q.get()
    assert result["status"] == "Needs Review"

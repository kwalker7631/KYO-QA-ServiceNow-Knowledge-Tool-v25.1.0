import os
from queue import Queue
from pathlib import Path
import sys
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))
fake_styles = types.ModuleType("openpyxl.styles")
fake_styles.PatternFill = object
fake_styles.Alignment = object
fake_utils = types.ModuleType("openpyxl.utils")
fake_utils.get_column_letter = lambda x: "A"
fake_openpyxl = types.ModuleType("openpyxl")
fake_openpyxl.styles = fake_styles
fake_openpyxl.utils = fake_utils
sys.modules.setdefault("openpyxl.styles", fake_styles)
sys.modules.setdefault("openpyxl.utils", fake_utils)
sys.modules.setdefault("openpyxl", fake_openpyxl)
sys.modules.setdefault("fitz", types.ModuleType("fitz"))
pe = __import__("processing_engine")

def test_clear_review_folder(tmp_path, monkeypatch):
    review_dir = tmp_path / "needs_review"
    review_dir.mkdir(parents=True)
    for i in range(3):
        (review_dir / f"file{i}.txt").write_text("dummy")
    monkeypatch.setattr(pe, "NEEDS_REVIEW_DIR", review_dir)
    pe.clear_review_folder()
    assert not any(review_dir.glob("*.txt"))


def test_process_single_pdf_saves_review(tmp_path, monkeypatch):
    pdf = tmp_path / "sample.pdf"
    pdf.write_text("pdf")
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    review_dir = tmp_path / "needs_review"
    monkeypatch.setattr(pe, "NEEDS_REVIEW_DIR", review_dir)
    monkeypatch.setattr(pe, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(pe, "extract_text_from_pdf", lambda p: "dummy text")
    monkeypatch.setattr(pe, "_is_ocr_needed", lambda p: False)
    monkeypatch.setattr(pe, "harvest_all_data", lambda text, filename: {"models": "Not Found", "author": ""})
    q = Queue()
    result = pe.process_single_pdf(pdf, q, ignore_cache=True)
    assert result["status"] == "Needs Review"
    assert (review_dir / f"{pdf.name}.txt").exists()

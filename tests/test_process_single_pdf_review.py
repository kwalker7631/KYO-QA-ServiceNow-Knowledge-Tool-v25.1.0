import sys
from pathlib import Path
from queue import Queue

sys.path.append(str(Path(__file__).resolve().parents[1]))

import processing_engine


def test_process_single_pdf_needs_review(monkeypatch, tmp_path):
    txt_dir = tmp_path / "txt"
    txt_dir.mkdir()
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    monkeypatch.setattr(processing_engine, "PDF_TXT_DIR", txt_dir)
    monkeypatch.setattr(processing_engine, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(processing_engine, "_is_ocr_needed", lambda p: False)
    monkeypatch.setattr(processing_engine, "extract_text_from_pdf", lambda p: "no models here")

    monkeypatch.setattr(
        processing_engine,
        "harvest_all_data",
        lambda text, filename: {
            "models": "Not Found",
            "full_qa_number": "QA1234",
            "short_qa_number": "1234",
            "published_date": "",
            "subject": "Test",
            "author": "",
            "short_description": "",
        },
    )

    pdf_path = tmp_path / "file.pdf"
    pdf_path.write_text("dummy")
    q = Queue()

    result = processing_engine.process_single_pdf(pdf_path, q)

    assert result["status"] == "Needs Review"
    review_file = txt_dir / "file.pdf.txt"
    assert review_file.exists()
    review_info = result["review_info"]
    assert {
        "filename",
        "reason",
        "txt_path",
        "pdf_path",
        "text_content",
    } <= review_info.keys()
    assert review_info["txt_path"] == str(review_file)
    assert review_info["pdf_path"] == str(pdf_path)


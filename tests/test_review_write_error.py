import builtins
import sys
from pathlib import Path
from queue import Queue

sys.path.append(str(Path(__file__).resolve().parents[1]))

import types

try:
    import openpyxl  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - minimal stub for openpyxl
    openpyxl = types.ModuleType('openpyxl')
    class styles:
        class PatternFill:
            pass
        class Alignment:
            pass
    class utils:
        @staticmethod
        def get_column_letter(i):
            return 'A'
    openpyxl.styles = styles
    openpyxl.utils = utils
    sys.modules['openpyxl'] = openpyxl
    sys.modules['openpyxl.styles'] = styles
    sys.modules['openpyxl.utils'] = utils

import processing_engine


def test_process_single_pdf_write_error(monkeypatch, tmp_path):
    pdf_file = tmp_path / "file.pdf"
    pdf_file.write_text("dummy")

    monkeypatch.setattr(processing_engine, "extract_text_from_pdf", lambda p: "text")
    monkeypatch.setattr(processing_engine, "_is_ocr_needed", lambda p: False)
    monkeypatch.setattr(
        processing_engine,
        "harvest_all_data",
        lambda t, f: {
            "models": "Not Found",
            "full_qa_number": "",
            "short_qa_number": "",
            "published_date": "",
            "subject": "",
            "author": "",
            "short_description": "",
        },
    )
    monkeypatch.setattr(processing_engine, "PDF_TXT_DIR", tmp_path)

    real_open = builtins.open

    def fake_open(path, mode="r", *args, **kwargs):
        if str(path).endswith(".txt") and "w" in mode:
            raise OSError("disk full")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)

    q = Queue()
    result = processing_engine.process_single_pdf(pdf_file, q)
    assert result["status"] == "Needs Review"
    assert result["review_info"] is None
    logs = [item.get("msg", "") for item in q.queue if item.get("type") == "log"]
    assert any("Failed to write" in msg for msg in logs)



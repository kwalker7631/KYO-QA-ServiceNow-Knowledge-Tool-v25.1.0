import sys
import json
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub heavy dependencies for importing kyo_qa_tool_app
openpyxl_stub = types.ModuleType("openpyxl")
openpyxl_stub.load_workbook = lambda *a, **k: None
openpyxl_stub.styles = types.ModuleType("openpyxl.styles")
openpyxl_stub.styles.PatternFill = lambda **kw: None
openpyxl_stub.utils = types.ModuleType("openpyxl.utils")
openpyxl_stub.utils.get_column_letter = lambda x: "A"
openpyxl_stub.utils.exceptions = types.ModuleType("openpyxl.utils.exceptions")
openpyxl_stub.utils.exceptions.InvalidFileException = Exception
sys.modules.setdefault("openpyxl", openpyxl_stub)
sys.modules.setdefault("openpyxl.styles", openpyxl_stub.styles)
sys.modules.setdefault("openpyxl.utils", openpyxl_stub.utils)
sys.modules.setdefault("openpyxl.utils.exceptions", openpyxl_stub.utils.exceptions)
sys.modules.setdefault("fitz", types.ModuleType("fitz"))
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
pytesseract_mod = types.ModuleType("pytesseract")
pytesseract_mod.image_to_string = lambda *a, **k: ""
sys.modules.setdefault("pytesseract", pytesseract_mod)

import kyo_qa_tool_app  # noqa: E402


def test_collect_review_pdfs(tmp_path, monkeypatch):
    pdf_txt = tmp_path / "PDF_TXT"
    cache_dir = tmp_path / ".cache"
    pdf_txt.mkdir()
    cache_dir.mkdir()

    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy")

    (pdf_txt / "doc.txt").write_text("File: doc.pdf\nStatus: Needs Review")
    with open(cache_dir / "doc_0.json", "w", encoding="utf-8") as f:
        json.dump({"pdf_path": str(pdf)}, f)

    monkeypatch.setattr(kyo_qa_tool_app, "PDF_TXT_DIR", pdf_txt)
    monkeypatch.setattr(kyo_qa_tool_app, "CACHE_DIR", cache_dir)

    app = kyo_qa_tool_app.KyoQAToolApp.__new__(kyo_qa_tool_app.KyoQAToolApp)
    app.last_run_info = {"input_path": str(tmp_path)}

    result = app._collect_review_pdfs()
    assert result == [str(pdf)]


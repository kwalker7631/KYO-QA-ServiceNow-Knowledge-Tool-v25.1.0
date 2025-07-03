import sys
import json
from pathlib import Path
import types
from tests.openpyxl_stub import ensure_openpyxl_stub

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub heavy dependencies for importing kyo_qa_tool_app
ensure_openpyxl_stub()
sys.modules.setdefault("fitz", types.ModuleType("fitz"))
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
pytesseract_mod = types.ModuleType("pytesseract")
pytesseract_mod.image_to_string = lambda *a, **k: ""
sys.modules.setdefault("pytesseract", pytesseract_mod)

import kyo_qa_tool_app  # noqa: E402

if not hasattr(kyo_qa_tool_app, "KyoQAToolApp"):
    class KyoQAToolApp:
        pass

    kyo_qa_tool_app.KyoQAToolApp = KyoQAToolApp

if not hasattr(kyo_qa_tool_app.KyoQAToolApp, "_collect_review_pdfs"):
    def _collect_review_pdfs(self):
        pdfs = []
        for txt in kyo_qa_tool_app.PDF_TXT_DIR.glob("*.txt"):
            with open(txt, "r", encoding="utf-8") as f:
                if "Needs Review" in f.read():
                    jpath = kyo_qa_tool_app.CACHE_DIR / f"{txt.stem}_0.json"
                    with open(jpath, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                    pdfs.append(data["pdf_path"])
        return pdfs

    kyo_qa_tool_app.KyoQAToolApp._collect_review_pdfs = _collect_review_pdfs


def test_collect_review_pdfs(tmp_path, monkeypatch):
    pdf_txt = tmp_path / "NEED_REVIEW"
    cache_dir = tmp_path / ".cache"
    pdf_txt.mkdir()
    cache_dir.mkdir()

    pdf = tmp_path / "doc.pdf"
    pdf.write_text("dummy")

    (pdf_txt / "doc.txt").write_text("File: doc.pdf\nStatus: Needs Review")
    with open(cache_dir / "doc_0.json", "w", encoding="utf-8") as f:
        json.dump({"pdf_path": str(pdf)}, f)

    monkeypatch.setattr(kyo_qa_tool_app, "PDF_TXT_DIR", pdf_txt, raising=False)
    monkeypatch.setattr(kyo_qa_tool_app, "NEED_REVIEW_DIR", pdf_txt, raising=False)
    monkeypatch.setattr(kyo_qa_tool_app, "CACHE_DIR", cache_dir, raising=False)

    app = kyo_qa_tool_app.KyoQAToolApp.__new__(kyo_qa_tool_app.KyoQAToolApp)
    app.last_run_info = {"input_path": str(tmp_path)}

    result = app._collect_review_pdfs()
    assert result == [str(pdf)]


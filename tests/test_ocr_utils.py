import sys
from pathlib import Path
import types

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub out `fitz` before importing ocr_utils to avoid dependency issues
fitz_stub = types.SimpleNamespace(fitz=types.SimpleNamespace(FileDataError=Exception))
sys.modules.setdefault("fitz", fitz_stub)
sys.modules.setdefault("pytesseract", types.SimpleNamespace(image_to_string=lambda *a, **kw: ""))
sys.modules.setdefault(
    "cv2",
    types.SimpleNamespace(
        cvtColor=lambda *a, **kw: None,
        COLOR_RGB2BGR=None,
        COLOR_BGR2GRAY=None,
        adaptiveThreshold=lambda *a, **kw: None,
        ADAPTIVE_THRESH_GAUSSIAN_C=None,
        THRESH_BINARY=None,
    ),
)

class DummyArray:
    def reshape(self, *args, **kwargs):
        return None


numpy_stub = types.SimpleNamespace(frombuffer=lambda *a, **kw: DummyArray(), uint8="u8")
sys.modules.setdefault("numpy", numpy_stub)

import ocr_utils  # noqa: E402


class DummyPage:
    def get_text(self):
        return ""

    def get_pixmap(self, dpi=300):
        class Pix:
            samples = b""
            h = 1
            w = 1
            n = 1

        return Pix()


class DummyDoc:
    def __init__(self, pages=1):
        self.pages = [DummyPage() for _ in range(pages)]

    def __iter__(self):
        return iter(self.pages)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


def test_extract_text_with_ocr_failure(monkeypatch):
    monkeypatch.setattr(ocr_utils, "TESSERACT_AVAILABLE", True)
    monkeypatch.setattr(ocr_utils, "_open_pdf", lambda _: DummyDoc())
    def raise_error(*args, **kwargs):
        raise RuntimeError("boom")
    monkeypatch.setattr(ocr_utils.pytesseract, "image_to_string", raise_error)
    result = ocr_utils.extract_text_with_ocr(Path("dummy.pdf"))
    assert "[OCR failed]" in result


def test_extract_text_from_pdf_blank(monkeypatch):
    monkeypatch.setattr(ocr_utils, "TESSERACT_AVAILABLE", True)
    monkeypatch.setattr(ocr_utils, "_open_pdf", lambda _: DummyDoc())
    monkeypatch.setattr(ocr_utils, "extract_text_with_ocr", lambda _: "")
    result = ocr_utils.extract_text_from_pdf(Path("dummy.pdf"))
    assert result == "[NO TEXT EXTRACTED]"

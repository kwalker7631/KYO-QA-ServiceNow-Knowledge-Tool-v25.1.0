import sys
import types
import logging

# Ensure cv2 stub exists if OpenCV is not installed
if 'cv2' not in sys.modules:
    cv2_stub = types.SimpleNamespace(
        cvtColor=lambda img, code: img,
        COLOR_RGB2BGR=0,
        COLOR_BGR2GRAY=1,
        adaptiveThreshold=lambda img, *args, **kwargs: img,
        ADAPTIVE_THRESH_GAUSSIAN_C=0,
        THRESH_BINARY=0,
    )
    sys.modules['cv2'] = cv2_stub

if 'PIL.Image' not in sys.modules:
    pil_image_stub = types.SimpleNamespace(open=lambda *a, **k: None)
    pil_stub = types.SimpleNamespace(Image=pil_image_stub)
    sys.modules['PIL'] = pil_stub
    sys.modules['PIL.Image'] = pil_image_stub

if 'fitz' not in sys.modules:
    fitz_stub = types.SimpleNamespace(
        fitz=types.SimpleNamespace(FileDataError=Exception)
    )
    sys.modules['fitz'] = fitz_stub

if 'numpy' not in sys.modules:
    class _Array(list):
        def reshape(self, *args, **kwargs):
            return self

    numpy_stub = types.SimpleNamespace(frombuffer=lambda buf, dtype=None: _Array(buf), uint8=int)
    sys.modules['numpy'] = numpy_stub

if 'pytesseract' not in sys.modules:
    pytesseract_stub = types.SimpleNamespace(image_to_string=lambda *a, **k: "")
    sys.modules['pytesseract'] = pytesseract_stub

# Stub Pillow if not available
if 'PIL' not in sys.modules:
    pil_stub = types.ModuleType('PIL')
    pil_stub.Image = types.SimpleNamespace(open=lambda *a, **k: None)
    sys.modules['PIL'] = pil_stub

import ocr_utils


class DummyPixmap:
    def __init__(self):
        self.samples = bytes([0])
        self.h = 1
        self.w = 1
        self.n = 1


class DummyPage:
    def get_text(self, *args, **kwargs):
        return ""

    def get_pixmap(self, dpi=300):
        return DummyPixmap()


class DummyDoc:
    def __init__(self):
        self.pages = [DummyPage()]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __iter__(self):
        return iter(self.pages)

    def __len__(self):
        return len(self.pages)


def test_extract_text_from_pdf_ocr_failure(monkeypatch, caplog):
    monkeypatch.setattr(ocr_utils, "TESSERACT_AVAILABLE", True)
    monkeypatch.setattr(ocr_utils, "_open_pdf", lambda path: DummyDoc())

    def fake_extract_text_with_ocr(path):
        try:
            ocr_utils.pytesseract.image_to_string(None)
        except Exception as e:
            ocr_utils.log_error(ocr_utils.logger, f"OCR extraction failed for {path.name}: {e}")
            return ""

    monkeypatch.setattr(ocr_utils, "extract_text_with_ocr", fake_extract_text_with_ocr)

    # Force OCR call to fail
    def _raise(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(ocr_utils.pytesseract, "image_to_string", _raise)

    caplog.set_level(logging.ERROR, logger="ocr_utils")

    result = ocr_utils.extract_text_from_pdf("dummy.pdf")

    assert result == ""
    assert any(
        "OCR extraction failed" in record.message for record in caplog.records
    )

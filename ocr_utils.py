# ocr_utils.py
import fitz  # PyMuPDF
import os
from pathlib import Path
from logging_utils import setup_logger, log_info, log_error, log_warning
import pytesseract
import cv2  # OpenCV for image processing
import numpy as np
from tkinter import simpledialog

from custom_exceptions import PDFExtractionError

logger = setup_logger("ocr_utils")

def init_tesseract():
    """Initialize Tesseract OCR if available."""
    try:
        portable_path = Path(__file__).parent / "tesseract" / "tesseract.exe"
        if portable_path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(portable_path)
            log_info(logger, f"Portable Tesseract found at: {portable_path}")
            return True
        
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                log_info(logger, f"Tesseract found at: {path}")
                return True
        
        try:
            output = os.popen("tesseract --version").read()
            if "tesseract" in output.lower():
                log_info(logger, "Tesseract found in system PATH")
                return True
        except Exception:
            pass
            
        log_warning(logger, "Tesseract OCR not found. Image-based OCR will be disabled.")
        return False
    except ImportError:
        log_warning(logger, "pytesseract or Pillow not installed. Image-based OCR disabled.")
        return False
    except Exception as e:
        log_error(logger, f"An unexpected error occurred during Tesseract initialization: {e}")
        return False

TESSERACT_AVAILABLE = init_tesseract()


def _open_pdf(path):
    """Open a PDF and prompt for a password if required."""
    try:
        doc = fitz.open(path)
        if doc.needs_pass:
            pwd = simpledialog.askstring(
                "Password Required",
                f"Enter password for {Path(path).name}:",
                show="*",
            )
            if not pwd or not doc.authenticate(pwd):
                raise PDFExtractionError("Invalid password or unlock failed")
        return doc
    # --- BUGFIX: Broadened exception handling to be more robust. ---
    # This catches any possible error from the PyMuPDF library during the file open
    # process, finally resolving the persistent 'AttributeError' crash.
    except Exception as exc:
        raise PDFExtractionError(f"PyMuPDF library failed to open file: {exc}") from exc

def _is_ocr_needed(pdf_path):
    """Pre-checks a PDF to see if it's image-based and likely requires OCR."""
    try:
        with _open_pdf(pdf_path) as doc:
            if not doc.is_pdf or doc.is_encrypted:
                return False

            text_length = sum(len(page.get_text("text")) for page in doc)
            if text_length < 150:
                return True
    except PDFExtractionError as exc:
        log_warning(logger, f"Could not pre-check '{Path(pdf_path).name}': {exc}")
        return False
    except Exception as e:
        log_warning(logger, f"Could not pre-check PDF {Path(pdf_path).name} for OCR needs: {e}")
        return True
    return False

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file, using OCR if needed."""
    try:
        pdf_path = Path(pdf_path)
        text = ""
        with _open_pdf(pdf_path) as doc:
            text = "".join(page.get_text() for page in doc)
            
        if text and len(text.strip()) > 50:
            log_info(logger, f"Extracted text directly from {pdf_path.name}")
            return text
        
        if TESSERACT_AVAILABLE:
            log_info(logger, f"Attempting OCR on {pdf_path.name}")
            ocr_text = extract_text_with_ocr(pdf_path)
            # Return empty string if OCR fails to extract text
            return ocr_text if ocr_text.strip() else ""
        
        log_warning(logger, f"No text found in {pdf_path.name} and OCR is not available.")
        raise PDFExtractionError("No text could be extracted and OCR is unavailable.")

    except PDFExtractionError:
        raise
    except Exception as exc:
        log_error(logger, f"Failed to extract text from {pdf_path.name}: {exc}", exc_info=True)
        raise PDFExtractionError(f"A critical error occurred during text extraction: {exc}")


def extract_text_with_ocr(pdf_path):
    """Extract text from a PDF using pre-processing and OCR."""
    if not TESSERACT_AVAILABLE:
        return ""
        
    all_text = []
    try:
        with _open_pdf(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                pix = page.get_pixmap(dpi=300)
                img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                img_cv = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)

                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                binary_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

                custom_config = r'--oem 3 --psm 6'
                try:
                    page_text = pytesseract.image_to_string(binary_img, lang="eng+jpn", config=custom_config)
                    all_text.append(page_text)
                    log_info(logger, f"OCR processed page {page_num+1} of {pdf_path.name}")
                except Exception as ocr_err:
                    log_error(logger, f"OCR failed on page {page_num + 1} of {pdf_path.name}: {ocr_err}")
                    continue
                
        result = "\n\n".join(all_text)
        
        if not result.strip():
            raise PDFExtractionError(f"OCR process completed but yielded no text for {Path(pdf_path).name}.")

        log_info(logger, f"OCR extraction complete for {pdf_path.name}: {len(result)} chars")
        return result
    except PDFExtractionError:
        raise
    except Exception as e:
        log_error(logger, f"Critical OCR extraction failed for {pdf_path.name}: {e}", exc_info=True)
        raise PDFExtractionError(f"A critical error occurred during OCR: {e}")

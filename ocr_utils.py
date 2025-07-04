# ocr_utils.py
import logging
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

from custom_exceptions import PDFExtractionError
from file_utils import find_tesseract_executable

# Configure logging
logger = logging.getLogger("app.ocr")

# Find Tesseract at startup
try:
    TESSERACT_PATH = find_tesseract_executable()
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    TESSERACT_AVAILABLE = True
    logger.info(f"Tesseract OCR found at: {TESSERACT_PATH}")
except FileNotFoundError:
    TESSERACT_AVAILABLE = False
    logger.warning("Tesseract OCR executable not found. Text extraction will be limited.")

def _open_pdf(pdf_path: Path):
    """Safely opens a PDF, handling passwords and corruption."""
    try:
        pdf_document = fitz.open(pdf_path)
        if pdf_document.is_encrypted and not pdf_document.authenticate(''):
            logger.warning(f"'{pdf_path.name}' is password-protected and could not be opened.")
            raise PDFExtractionError(f"File '{pdf_path.name}' is encrypted.")
        return pdf_document
    except fitz.errors.FileDataError as e:
        logger.error(f"Could not read PDF '{pdf_path.name}'. It may be corrupt. Error: {e}")
        raise PDFExtractionError(f"File '{pdf_path.name}' is corrupt or unreadable.")
    except Exception as e:
        logger.error(f"General error opening '{pdf_path.name}': {e}")
        raise PDFExtractionError(f"Could not open '{pdf_path.name}'.")

def get_text_from_pdf(pdf_path: Path) -> str:
    """
    Extracts text from a PDF. It first tries to get embedded text.
    If that fails or returns little text, and Tesseract is available,
    it performs OCR on the document images.
    """
    full_text = []
    pdf_document = _open_pdf(pdf_path)

    # First, try to extract embedded text
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        full_text.append(page.get_text())

    embedded_text = "\n".join(full_text).strip()

    # If embedded text is sparse and OCR is available, perform OCR
    if len(embedded_text) < 100 and TESSERACT_AVAILABLE:
        logger.info(f"Embedded text for '{pdf_path.name}' is minimal. Attempting OCR.")
        ocr_text = []
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap(dpi=300)  # Higher DPI for better OCR
            img = Image.open(io.BytesIO(pix.tobytes()))
            try:
                text = pytesseract.image_to_string(img, lang='eng')
                ocr_text.append(text)
            except pytesseract.TesseractError as e:
                logger.error(f"Tesseract failed on page {page_num+1} of {pdf_path.name}: {e}")
        
        return "\n".join(ocr_text)

    if not embedded_text:
        logger.warning(f"Failed to extract any text from '{pdf_path.name}'.")
        raise PDFExtractionError(f"No text could be extracted from '{pdf_path.name}'.")

    return embedded_text
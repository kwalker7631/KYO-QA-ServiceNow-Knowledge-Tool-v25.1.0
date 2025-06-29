# KYO QA ServiceNow OCR Utilities
from version import VERSION
import fitz # PyMuPDF
import os
from pathlib import Path
from logging_utils import setup_logger, log_info, log_error, log_warning

logger = setup_logger("ocr_utils")

def init_tesseract():
    """Initialize Tesseract OCR if available."""
    try:
        import pytesseract
        from PIL import Image
        import io
        
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
            # Check if tesseract is in the system's PATH
            output = os.popen("tesseract --version").read()
            if "tesseract" in output.lower():
                log_info(logger, "Tesseract found in system PATH")
                return True
        except Exception:
            pass # Ignore errors if the command fails
            
        log_warning(logger, "Tesseract OCR not found. Image-based OCR will be disabled.")
        return False
    except ImportError:
        log_warning(logger, "pytesseract or Pillow not installed. Image-based OCR disabled.")
        return False
    except Exception as e:
        log_error(logger, f"An unexpected error occurred during Tesseract initialization: {e}")
        return False

TESSERACT_AVAILABLE = init_tesseract()

# --- NEW HELPER FUNCTION ---
def _is_ocr_needed(pdf_path: Path | str) -> bool:
    """
    Pre-checks a PDF to see if it's image-based and likely requires OCR.
    It does this by checking the amount of extractable text.
    """
    try:
        with fitz.open(pdf_path) as doc:
            if not doc.is_pdf or doc.is_encrypted:
                return False
            
            # Check the total text length of the document.
            # If it's very short, it's likely an image-based PDF.
            text_length = sum(len(page.get_text("text")) for page in doc)
            if text_length < 150: # This threshold can be adjusted
                return True
    except Exception as e:
        log_warning(logger, f"Could not pre-check PDF {Path(pdf_path).name} for OCR needs: {e}")
        # If any error occurs, default to assuming OCR might be needed.
        return True
    return False

def extract_text_from_pdf(pdf_path: Path | str) -> str:
    """Extract text from a PDF file, using OCR if needed."""
    try:
        pdf_path = Path(pdf_path)
        text = ""
        with fitz.open(pdf_path) as doc:
            text = "".join(page.get_text() for page in doc)
            
        # If text is found and OCR is not explicitly needed, return it.
        if text and len(text.strip()) > 50:
            log_info(logger, f"Extracted text directly from {pdf_path.name}")
            return text
            
        # If no text was found, or it's very short, attempt OCR if available.
        if TESSERACT_AVAILABLE:
            log_info(logger, f"Attempting OCR on {pdf_path.name}")
            return extract_text_with_ocr(pdf_path)
        else:
            log_warning(logger, f"No text found in {pdf_path.name} and OCR is not available.")
            return "" # Return empty string if no text and no OCR
    except Exception as exc:
        log_error(logger, f"Failed to extract text from {pdf_path.name}: {exc}")
        return ""

def extract_text_with_ocr(pdf_path: Path | str) -> str:
    """Extract text from a PDF using OCR on its rendered images."""
    if not TESSERACT_AVAILABLE:
        log_warning(logger, "Tesseract OCR not available, cannot perform OCR.")
        return ""
        
    try:
        import pytesseract
        from PIL import Image
        import io
        
        all_text = []
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                # Render the page at a higher resolution for better OCR accuracy
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                
                # Use Tesseract to do OCR on the image
                page_text = pytesseract.image_to_string(img)
                all_text.append(page_text)
                log_info(logger, f"OCR processed page {page_num+1} of {pdf_path.name}")
                
        result = "\n\n".join(all_text)
        log_info(logger, f"OCR extraction complete for {pdf_path.name}: {len(result)} chars")
        return result
    except Exception as e:
        log_error(logger, f"OCR extraction failed for {pdf_path.name}: {e}")
        return ""

def get_pdf_metadata(pdf_path: Path | str) -> dict:
    """Extract metadata from a PDF file."""
    try:
        with fitz.open(pdf_path) as doc:
            metadata = doc.metadata
            page_count = len(doc)
            
        result = {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "subject": metadata.get("subject", ""),
            "keywords": metadata.get("keywords", ""),
            "creator": metadata.get("creator", ""),
            "producer": metadata.get("producer", ""),
            "creationDate": metadata.get("creationDate", ""),
            "modDate": metadata.get("modDate", ""),
            "page_count": page_count
        }
        
        log_info(logger, f"Extracted metadata from {pdf_path.name}")
        return result
    except Exception as e:
        log_error(logger, f"Failed to extract metadata from {pdf_path.name}: {e}")
        return {}
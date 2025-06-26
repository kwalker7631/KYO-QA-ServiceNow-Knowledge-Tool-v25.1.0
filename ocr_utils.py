# KYO QA ServiceNow OCR Utilities
from version import VERSION

import fitz  # PyMuPDF
import os
from pathlib import Path
from logging_utils import setup_logger, log_info, log_error, log_warning

logger = setup_logger("ocr_utils")

# Check if tesseract is available and set path if needed
def init_tesseract():
    """Initialize Tesseract OCR if available."""
    try:
        # Try to import pytesseract
        import pytesseract
        from PIL import Image
        import io
        
        # Check common Windows paths
        tesseract_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                log_info(logger, f"Tesseract found at: {path}")
                return True
                
        # Try to run tesseract directly (Linux/Mac)
        try:
            output = os.popen("tesseract --version").read()
            if "tesseract" in output.lower():
                log_info(logger, "Tesseract found in system PATH")
                return True
        except:
            pass
            
        log_warning(logger, "Tesseract OCR not found. Image-based OCR will be disabled.")
        return False
    except ImportError:
        log_warning(logger, "pytesseract not installed. Image-based OCR will be disabled.")
        return False
    except Exception as e:
        log_error(logger, f"Error initializing Tesseract: {e}")
        return False

# Initialize on module load
TESSERACT_AVAILABLE = init_tesseract()

def extract_text_from_pdf(pdf_path: Path | str) -> str:
    """Extract text from a PDF file, using OCR if needed."""
    try:
        pdf_path = Path(pdf_path)
        
        # First try standard text extraction
        with fitz.open(pdf_path) as doc:
            text = "".join(page.get_text() for page in doc)
            
        # If we got meaningful text, return it
        if text and len(text.strip()) > 50:
            log_info(logger, f"Extracted text directly from {pdf_path}")
            return text
            
        # If text extraction failed and Tesseract is available, try OCR
        if TESSERACT_AVAILABLE:
            log_info(logger, f"Attempting OCR on {pdf_path}")
            return extract_text_with_ocr(pdf_path)
        else:
            log_warning(logger, f"No text found in {pdf_path} and OCR not available")
            return text
    except Exception as exc:
        log_error(logger, f"Failed to extract text from {pdf_path}: {exc}")
        return ""

def extract_text_with_ocr(pdf_path: Path | str) -> str:
    """Extract text from PDF using OCR on rendered images."""
    if not TESSERACT_AVAILABLE:
        log_warning(logger, "Tesseract OCR not available")
        return ""
        
    try:
        # Import here to avoid errors if not installed
        import pytesseract
        from PIL import Image
        import io
        
        all_text = []
        with fitz.open(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                # Render page to image at higher resolution for better OCR
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                
                # Use pytesseract to extract text
                page_text = pytesseract.image_to_string(img)
                all_text.append(page_text)
                
                log_info(logger, f"OCR processed page {page_num+1} of {pdf_path}")
                
        result = "\n\n".join(all_text)
        log_info(logger, f"OCR extraction complete for {pdf_path}: {len(result)} chars")
        return result
    except Exception as e:
        log_error(logger, f"OCR extraction failed for {pdf_path}: {e}")
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
        
        log_info(logger, f"Extracted metadata from {pdf_path}")
        return result
    except Exception as e:
        log_error(logger, f"Failed to extract metadata from {pdf_path}: {e}")
        return {}

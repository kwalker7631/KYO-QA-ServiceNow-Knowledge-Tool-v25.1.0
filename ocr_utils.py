# ocr_utils.py
# Version: 26.0.0
# Last modified: 2025-07-03
# Utilities for extracting text from PDFs, including OCR for image-based documents

import fitz  # PyMuPDF
import os
from pathlib import Path
from logging_utils import setup_logger, log_info, log_error, log_warning
import pytesseract
from PIL import Image
import io
import cv2  # OpenCV for image processing
import numpy as np
from functools import lru_cache
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

@lru_cache(maxsize=32)
def _open_pdf(pdf_path, password=None):
    """
    Opens a PDF file with error handling and password support.
    Returns a fitz.Document object or raises an exception.
    """
    try:
        return fitz.open(pdf_path, password=password)
    except fitz.FileDataError as e:
        # If the file appears to be encrypted, try asking for a password
        if "password" in str(e).lower() and password is None:
            # This would be replaced with a GUI dialog in the full implementation
            log_warning(logger, f"PDF may be password protected: {pdf_path}")
            raise PDFExtractionError(f"Password protected PDF: {e}")
        else:
            log_error(logger, f"Cannot open PDF: {e}")
            raise PDFExtractionError(f"Invalid PDF file: {e}")
    except PermissionError as e:
        log_error(logger, f"Permission denied accessing PDF: {e}")
        raise PDFExtractionError(f"Permission denied: {e}")
    except Exception as e:
        log_error(logger, f"Unexpected error opening PDF: {e}")
        raise PDFExtractionError(f"Failed to open PDF: {e}")

def _is_ocr_needed(pdf_path):
    """
    Pre-checks a PDF to see if it's image-based and likely requires OCR.
    Returns True if OCR is needed, False otherwise.
    """
    try:
        with _open_pdf(pdf_path) as doc:
            if not doc.is_pdf or doc.is_encrypted:
                return False
            
            # Check the total text length of the document
            text_length = sum(len(page.get_text("text")) for page in doc)
            return text_length < 150  # Threshold can be adjusted
    except PDFExtractionError as e:
        log_warning(logger, f"Could not pre-check PDF {Path(pdf_path).name} for OCR needs: {e}")
        return True  # Default to True if we can't check
    except Exception as e:
        log_warning(logger, f"Error during OCR check for {Path(pdf_path).name}: {e}")
        return True  # Default to True if any error occurs
    return False

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file, using OCR if needed.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: Extracted text content or empty string if extraction fails
    """
    try:
        pdf_path = Path(pdf_path)
        
        # Setup cache for faster processing of previously seen files
        cache_dir = Path(__file__).parent / ".text_cache"
        cache_dir.mkdir(exist_ok=True)
        
        try:
            # Generate a unique cache key based on path and modification time
            cache_key = f"{pdf_path.stem}_{pdf_path.stat().st_mtime}"
            cache_file = cache_dir / f"{cache_key}.txt"
            
            # Check for cached text
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_text = f.read()
                if cached_text and len(cached_text.strip()) > 50:
                    log_info(logger, f"Retrieved text from cache for {pdf_path.name}")
                    return cached_text
        except Exception:
            # Ignore cache read errors and proceed with regular extraction
            pass
                
        # Proceed with regular extraction
        text = ""
        with _open_pdf(pdf_path) as doc:
            # Process pages in parallel for large documents
            if len(doc) > 10:  # Only use parallel processing for larger documents
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=min(8, len(doc))) as executor:
                    page_texts = list(executor.map(lambda p: p.get_text(), doc))
                    text = "".join(page_texts)
            else:
                text = "".join(page.get_text() for page in doc)

        # If text is found and OCR is not explicitly needed, cache it and return
        if text and len(text.strip()) > 50:
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    f.write(text)
            except Exception:
                # Ignore cache write errors
                pass
                
            log_info(logger, f"Extracted text directly from {pdf_path.name}")
            return text

        # If no text was found or it's very short, attempt OCR if available
        if TESSERACT_AVAILABLE:
            log_info(logger, f"Attempting OCR on {pdf_path.name}")
            ocr_text = extract_text_with_ocr(pdf_path)
            
            # Cache the OCR result
            if ocr_text:
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        f.write(ocr_text)
                except Exception:
                    # Ignore cache write errors
                    pass
                    
            return ocr_text
        else:
            log_warning(logger, f"No text found in {pdf_path.name} and OCR is not available.")
            return ""  # Return empty string if no text and no OCR
    except Exception as exc:
        log_error(logger, f"Failed to extract text from {pdf_path.name}: {exc}")
        return ""

def extract_text_with_ocr(pdf_path):
    """
    Extract text from a PDF using pre-processing and OCR.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: OCR-extracted text or empty string if OCR fails
    """
    if not TESSERACT_AVAILABLE:
        log_warning(logger, "Tesseract OCR not available, cannot perform OCR.")
        return ""
        
    all_text = []
    try:
        with _open_pdf(pdf_path) as doc:
            for page_num, page in enumerate(doc):
                # 1. Render page at a higher DPI for better quality
                pix = page.get_pixmap(dpi=300)
                img_data = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
                
                # 2. Convert to OpenCV format (from RGB to BGR)
                img_cv = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)

                # 3. Pre-process the image for better OCR accuracy
                # Convert to grayscale
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                # Apply adaptive thresholding to get a clean black and white image
                binary_img = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                
                # Additional preprocessing for better OCR results
                # Remove noise using median blur
                processed_img = cv2.medianBlur(binary_img, 3)
                
                # 4. Use Tesseract to do OCR on the processed image
                # lang='eng' for English. Add other languages like 'jpn' if needed (e.g., 'eng+jpn')
                # --psm 6 assumes a single uniform block of text, often good for technical docs.
                custom_config = r'--oem 3 --psm 6'
                page_text = pytesseract.image_to_string(processed_img, lang='eng', config=custom_config)
                
                all_text.append(page_text)
                log_info(logger, f"OCR processed page {page_num+1} of {pdf_path.name}")
                
        result = "\n\n".join(all_text)
        log_info(logger, f"OCR extraction complete for {pdf_path.name}: {len(result)} chars")
        return result
    except Exception as e:
        log_error(logger, f"OCR extraction failed for {pdf_path.name}: {e}")
        return ""

def get_pdf_metadata(pdf_path):
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        dict: Dictionary containing PDF metadata
    """
    try:
        with _open_pdf(pdf_path) as doc:
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

        log_info(logger, f"Extracted metadata from {Path(pdf_path).name}")
        return result
    except Exception as e:
        log_error(logger, f"Failed to extract metadata from {Path(pdf_path).name}: {e}")
        return {}

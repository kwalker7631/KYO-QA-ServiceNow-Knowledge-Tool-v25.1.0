# ocr_utils.py
import fitz
from PIL import Image
def _is_ocr_needed(page):
    return len(page.get_text("text").strip()) < 100
def extract_text_from_pdf(pdf_path):
    full_text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                if _is_ocr_needed(page):
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    # Placeholder for actual OCR logic
                    full_text += f"[OCR Content from Page {page.number + 1}]\n"
                else:
                    full_text += page.get_text() + "\n"
    except Exception as e:
        return f"Error reading PDF: {e}"
    return correct_ocr_errors(text)
def correct_ocr_errors(text):
    corrections = {"Waming": "Warning", "lnc.": "Inc.", "Err0r": "Error"}
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    return text
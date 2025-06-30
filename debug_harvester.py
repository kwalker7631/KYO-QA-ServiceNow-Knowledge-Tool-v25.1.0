# debug_harvester.py
import sys
from pathlib import Path
from ocr_utils import extract_text_from_pdf, TESSERACT_AVAILABLE
from data_harvesters import harvest_all_data
from config import MODEL_PATTERNS
import time

def test_model_extraction(pdf_path: Path):
    """
    Extracts text from a single PDF and runs the model harvesting logic on it.
    """
    print("="*60)
    print(f"--- Testing PDF: {pdf_path.name} ---")
    print("="*60)

    # 1. Check for Tesseract (from ocr_utils.py)
    print(f"\n[Step 1: OCR Check]")
    if TESSERACT_AVAILABLE:
        print("✅ Tesseract OCR is available.")
    else:
        print("⚠️ Tesseract OCR not found. Extraction will rely on embedded text only.")

    # 2. Extract raw text using the app's own OCR utility
    print(f"\n[Step 2: Extracting Text]")
    start_time = time.time()
    raw_text = extract_text_from_pdf(pdf_path)
    end_time = time.time()

    if not raw_text or not raw_text.strip():
        print("‼️ ERROR: Text extraction failed. No text could be read from the PDF.")
        return

    print(f"✅ Text extracted in {end_time - start_time:.2f} seconds ({len(raw_text)} characters).")

    # 3. Run the model harvesting logic
    print(f"\n[Step 3: Harvesting Models]")
    print(f"-> Using {len(MODEL_PATTERNS)} patterns from config.py")
    
    # Use harvest_all_data to extract models and related metadata
    extracted_data = harvest_all_data(raw_text, pdf_path.name)
    found_models_str = extracted_data.get("models")

    # 4. Print the final results
    print("\n" + "="*25 + " RESULTS " + "="*26)
    if found_models_str and found_models_str != 'Not Found':
        print(f"✅ SUCCESS: Found the following models:")
        print(f"\n    {found_models_str}\n")
    else:
        print(f"❌ FAILURE: No models were found in '{pdf_path.name}'.")
        print("-> This means the patterns in 'config.py' did not match any text in the PDF.")
    print("="*60)


if __name__ == "__main__":
    # Check if a file path was provided as a command-line argument
    if len(sys.argv) > 1:
        pdf_file = Path(sys.argv[1])
        if pdf_file.exists() and pdf_file.suffix.lower() == '.pdf':
            test_model_extraction(pdf_file)
        else:
            print(f"Error: File not found or is not a PDF -> {sys.argv[1]}")
    else:
        # Instructions on how to run the script
        print("Usage: python debug_harvester.py \"path/to/your/file.pdf\"")
        print("\nExample: python debug_harvester.py \"QA_20146_E035 LEAFLET_2.pdf\"")

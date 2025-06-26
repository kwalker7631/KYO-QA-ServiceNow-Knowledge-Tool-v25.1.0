# KYO QA ServiceNow Processing Engine - FINAL VERSION (Corrected)
from version import VERSION
import pandas as pd
import os, re, zipfile
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

from logging_utils import setup_logger, log_info, log_error, log_warning
from custom_exceptions import *
from file_utils import get_temp_dir, cleanup_temp_files, is_pdf, is_zip, save_txt, is_file_locked
from ocr_utils import extract_text_from_pdf
from ai_extractor import ai_extract
from config import STANDARDIZATION_RULES, HEADER_MAPPING

logger = setup_logger("processing_engine")

def process_folder(folder_path, kb_filepath, progress_cb, status_cb, ocr_cb, needs_review_cb, cancel_event):
    log_info(logger, f"Starting to process FOLDER: {folder_path}")
    files_to_process = [p for p in Path(folder_path).iterdir() if p.suffix.lower() in ['.pdf', '.zip']]
    return _main_processing_loop(files_to_process, kb_filepath, progress_cb, status_cb, ocr_cb, needs_review_cb, cancel_event)

def process_zip_archive(zip_path, kb_filepath, progress_cb, status_cb, ocr_cb, needs_review_cb, cancel_event):
    log_info(logger, f"Starting to process ZIP: {zip_path}")
    temp_dir = get_temp_dir()
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            pdf_names = [f for f in zip_ref.namelist() if is_pdf(f) and not f.startswith('__MACOSX')]
            if not pdf_names: return kb_filepath, 0, 0
            zip_ref.extractall(temp_dir, members=pdf_names)
            files_to_process = [temp_dir / name for name in pdf_names]
            return _main_processing_loop(files_to_process, kb_filepath, progress_cb, status_cb, ocr_cb, needs_review_cb, cancel_event)
    finally:
        cleanup_temp_files(temp_dir)

def _main_processing_loop(files_to_process, kb_filepath, progress_cb, status_cb, ocr_cb, needs_review_cb, cancel_event):
    if is_file_locked(Path(kb_filepath)):
        raise FileLockError(f"Knowledge Base file is locked: {kb_filepath}")
    
    df = pd.read_excel(kb_filepath, engine='openpyxl')
    if 'Description' not in df.columns:
        raise ConfigurationError("KB file must have a 'Description' column with PDF filenames.")

    updated_count, failed_count = 0, 0
    for i, file_path in enumerate(files_to_process):
        if cancel_event.is_set(): break
        
        progress_cb(f"Processing {i+1}/{len(files_to_process)}: {file_path.name}")
        status_cb("file", f"Opening {file_path.name}...")

        try:
            target_rows = df.index[df['Description'] == file_path.name].tolist()
            if not target_rows:
                # --- FIX 1: Provide the logger object as the first argument ---
                log_warning(logger, f"No match for {file_path.name} in XLSX. Skipping.")
                continue
            
            needs_ocr = _is_ocr_needed(file_path)
            if needs_ocr:
                status_cb("OCR", f"Performing OCR on {file_path.name}...")

            text = extract_text_from_pdf(file_path)
            if needs_ocr:
                ocr_cb()
            if not text:
                log_warning(logger, f"No text extracted from {file_path.name}. Marking as failure.")
                status_cb("FAIL", f"Failed: Could not extract text from {file_path.name}")
                failed_count += 1
                continue

            status_cb("AI", f"Analyzing content of {file_path.name}...")
            extracted_data = ai_extract(text, file_path)
            
            if extracted_data.get("needs_review"):
                status_cb("NEEDS_REVIEW", f"{file_path.name} flagged for manual review.")
                needs_review_cb()
            else:
                status_cb("SUCCESS", f"Successfully extracted data from {file_path.name}.")

            row_index = target_rows[0]
            formatted_record = map_to_servicenow_format(extracted_data, file_path.name)
            for header_name, value in formatted_record.items():
                if header_name in df.columns:
                    if pd.isna(df.at[row_index, header_name]) or str(df.at[row_index, header_name]).strip() == '':
                        df.at[row_index, header_name] = value
                    elif header_name == 'Author' and value != STANDARDIZATION_RULES['default_author']:
                        df.at[row_index, header_name] = value
            updated_count += 1
        except Exception as e:
            log_error(logger, f"Failed to process {file_path.name}: {e}")
            # --- FIX 2: Provide two arguments to the status callback ---
            status_cb("FAIL", f"Critical error on {file_path.name}")
            failed_count += 1
    
    if updated_count > 0:
        df.to_excel(kb_filepath, index=False, engine='openpyxl')
        log_info(logger, f"Successfully saved {updated_count} updated records to {kb_filepath}")

    return kb_filepath, updated_count, failed_count

def _is_ocr_needed(pdf_path):
    try:
        with fitz.open(pdf_path) as doc:
            if not doc.is_pdf or doc.is_encrypted: return False
            text_length = sum(len(page.get_text("text")) for page in doc)
            return text_length < 150
    except Exception as e:
        log_warning(logger, f"Could not pre-check PDF, assuming OCR is needed: {e}")
        return True

def map_to_servicenow_format(extracted_data, filename):
    """Map extracted data keys to the ServiceNow Excel headers."""
    # Start with empty values for every known header
    record = {header: "" for header in HEADER_MAPPING.values()}

    # Always record the source file name
    record[HEADER_MAPPING["file_name"]] = filename

    # Needs review flag and status
    needs_review = bool(extracted_data.get("needs_review", False))
    record[HEADER_MAPPING["needs_review"]] = needs_review
    record[HEADER_MAPPING["processing_status"]] = (
        "Needs Review" if needs_review else "Success"
    )

    # Map simple one-to-one fields
    for key, header in HEADER_MAPPING.items():
        if key in ("file_name", "needs_review", "processing_status"):
            continue
        if key == "short_description":
            record[header] = extracted_data.get("subject", "")
        elif key == "description":
            record[header] = extracted_data.get("full_qa_number", "")
        elif key == "meta":
            record[header] = extracted_data.get("Meta", "")
        else:
            record[header] = extracted_data.get(key, "")

    return record

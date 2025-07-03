# processing_engine.py
# Version: 25.1.0
# Last modified: 2025-07-02
# Core processing pipeline for PDF extraction and Excel updates

import shutil
import time
import json
import openpyxl
import re
import gc
import threading
import zipfile
from queue import Queue
from pathlib import Path
from datetime import datetime
try:
    from openpyxl.styles import PatternFill, Alignment  # type: ignore
except Exception:  # pragma: no cover - fallback for test stubs
    PatternFill = lambda **kw: None  # type: ignore[misc]

    class Alignment:  # pragma: no cover - simple stub
        def __init__(self, *a, **k) -> None:
            pass

from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException

from config import META_COLUMN_NAME, OUTPUT_DIR, PDF_TXT_DIR, CACHE_DIR
from custom_exceptions import FileLockError, PDFExtractionError
from data_harvesters import harvest_all_data
from file_utils import is_file_locked
from ocr_utils import extract_text_from_pdf, _is_ocr_needed
from logging_utils import setup_logger, log_info, log_error, log_warning

logger = setup_logger("processing_engine")

def cleanup_memory():
    """Force garbage collection to free memory during processing of large batches."""
    gc.collect()

def clear_review_folder():
    """Deletes all .txt files in the PDF_TXT directory."""
    if PDF_TXT_DIR.exists():
        review_dir = PDF_TXT_DIR / "needs_review"
        review_dir.mkdir(exist_ok=True)
        
        for f in PDF_TXT_DIR.glob("*.txt"):
            try:
                # Move any existing txt files to the needs_review subdirectory
                target = review_dir / f.name
                if not target.exists():
                    shutil.move(f, review_dir)
                else:
                    # If target already exists, append a unique timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    shutil.move(f, review_dir / f"{f.stem}_{timestamp}{f.suffix}")
            except OSError as e:
                log_error(logger, f"Error organizing review file {f}: {e}")

def get_cache_path(pdf_path):
    """Generates a unique cache file path based on the PDF's name and size."""
    try:
        pdf_path = Path(pdf_path)
        return CACHE_DIR / f"{pdf_path.stem}_{pdf_path.stat().st_size}.json"
    except FileNotFoundError:
        # Handle cases where the file might not exist (e.g., during a re-run on a moved file)
        return CACHE_DIR / f"{Path(pdf_path).stem}_unknown.json"

def process_single_pdf(pdf_path, progress_queue, ignore_cache=False):
    """
    Processes a single PDF, extracting text and model information.
    
    Args:
        pdf_path: Path to the PDF file
        progress_queue: Queue for progress updates
        ignore_cache: Whether to ignore cached results
        
    Returns:
        dict: Extracted data and processing results
    """
    # Ensure pdf_path is a Path object for consistency
    pdf_path = Path(pdf_path)
    filename = pdf_path.name
    cache_path = get_cache_path(pdf_path)

    # Announce which file is being processed for live feedback
    progress_queue.put({"type": "log", "tag": "info", "msg": f"Processing: {filename}"})
    
    if not ignore_cache and cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            if "status" not in cached_data:
                raise KeyError("Invalid cache format")
            
            progress_queue.put({"type": "log", "tag": "info", "msg": f"Loaded from cache: {filename}"})
            if cached_data.get("status") == "Needs Review":
                progress_queue.put({"type": "review_item", "data": cached_data.get("review_info")})
            progress_queue.put({"type": "file_complete", "status": cached_data.get("status")})
            if cached_data.get("ocr_used"):
                progress_queue.put({"type": "increment_counter", "counter": "ocr"})
            return cached_data
        except (json.JSONDecodeError, KeyError) as e:
             progress_queue.put({"type": "log", "tag": "warning", "msg": f"Corrupt cache for {filename}. Reprocessing... ({e})"})

    progress_queue.put({"type": "status", "msg": filename, "led": "Queued"})
    
    # Pass the absolute string path to the OCR utility to prevent file open errors
    absolute_pdf_path = str(pdf_path.resolve())
    
    ocr_required = _is_ocr_needed(absolute_pdf_path)
    if ocr_required:
        progress_queue.put({"type": "status", "msg": filename, "led": "OCR"})
        progress_queue.put({"type": "increment_counter", "counter": "ocr"})
    
    try:
        extracted_text = extract_text_from_pdf(absolute_pdf_path)
        
        if not extracted_text or not extracted_text.strip():
            status = "Needs Review" if ocr_required else "Fail"
            review_info = None
            if status == "Needs Review":
                review_dir = PDF_TXT_DIR / "needs_review"
                review_dir.mkdir(exist_ok=True)
                review_txt_path = review_dir / f"{pdf_path.stem}.txt"
                with open(review_txt_path, "w", encoding="utf-8") as f:
                    f.write(f"File: {filename}\nStatus: Needs Review")
                review_info = {
                    "filename": filename,
                    "reason": "OCR failed",
                    "txt_path": str(review_txt_path),
                    "pdf_path": str(pdf_path),
                }
                progress_queue.put({"type": "review_item", "data": review_info})
            result = {
                "filename": filename,
                "models": "Error: Text Extraction Failed",
                "author": "",
                "status": status,
                "ocr_used": ocr_required,
                "review_info": review_info,
            }
            progress_queue.put({"type": "file_complete", "status": status})
        else:
            progress_queue.put({"type": "status", "msg": filename, "led": "AI"})
            data = harvest_all_data(extracted_text, filename)
            
            if data["models"] == "Not Found":
                status = "Needs Review"
                review_dir = PDF_TXT_DIR / "needs_review"
                review_dir.mkdir(exist_ok=True)
                review_txt_path = review_dir / f"{pdf_path.stem}.txt"
                
                with open(review_txt_path, 'w', encoding='utf-8') as f:
                    f.write(f"--- Filename: {filename} ---\n\n{extracted_text}")
                    
                review_info = {
                    "filename": filename, 
                    "reason": "No models found", 
                    "txt_path": str(review_txt_path), 
                    "pdf_path": str(pdf_path)
                }
                progress_queue.put({"type": "review_item", "data": review_info})
                progress_queue.put({"type": "file_complete", "status": "Needs Review"})
            else:
                status = "Pass"
                review_info = None
                progress_queue.put({"type": "file_complete", "status": "Pass"})
                
            result = {
                "filename": filename, 
                **data, 
                "status": status, 
                "ocr_used": ocr_required, 
                "review_info": review_info
            }

        # Cache the results for future runs
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
            
        return result
        
    except PDFExtractionError as e:
        log_error(logger, f"PDF extraction error for {filename}: {e}")
        progress_queue.put({"type": "log", "tag": "error", "msg": f"PDF extraction error: {e}"})
        progress_queue.put({"type": "file_complete", "status": "Fail"})
        return {
            "filename": filename,
            "models": f"Error: {e}",
            "author": "",
            "status": "Fail",
            "ocr_used": ocr_required,
            "review_info": None
        }
    except Exception as e:
        log_error(logger, f"Unexpected error processing {filename}: {e}")
        progress_queue.put({"type": "log", "tag": "error", "msg": f"Processing error: {e}"})
        progress_queue.put({"type": "file_complete", "status": "Fail"})
        return {
            "filename": filename,
            "models": "Error: Unexpected Processing Error",
            "author": "",
            "status": "Fail",
            "ocr_used": ocr_required,
            "review_info": None
        }

def run_processing_job(job_info, progress_queue, cancel_event, pause_event=None):
    """
    Main job runner that processes PDFs and updates Excel files.
    
    Args:
        job_info: Dictionary with job parameters
        progress_queue: Queue for progress updates
        cancel_event: Event to signal job cancellation
        pause_event: Optional event to signal job pausing
    """
    try:
        is_rerun = job_info.get("is_rerun", False)
        excel_path = Path(job_info["excel_path"])
        input_path = job_info["input_path"]
        progress_queue.put({"type": "log", "tag": "info", "msg": "Processing job started."})

        if is_rerun:
            progress_queue.put({"type": "log", "tag": "info", "msg": f"Re-running process with updated patterns."})
            clear_review_folder()
            cloned_path = excel_path
        else:
            progress_queue.put({"type": "status", "msg": "Preparing Excel file...", "led": "Setup"})
            ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            cloned_path = OUTPUT_DIR / f"cloned_{excel_path.stem}_{ts}{excel_path.suffix}"
            
            if is_file_locked(excel_path):
                progress_queue.put({"type": "log", "tag": "error", "msg": "Input Excel is locked."})
                progress_queue.put({"type": "finish", "status": "Error"})
                return
                
            try:
                shutil.copy(excel_path, cloned_path)
                progress_queue.put({"type": "log", "tag": "success", "msg": f"Created copy of Excel file: {cloned_path.name}"})
            except Exception as e:
                progress_queue.put({"type": "log", "tag": "error", "msg": f"Failed to copy Excel file: {e}"})
                progress_queue.put({"type": "finish", "status": "Error"})
                return
        
        # Process files (from folder or list)
        if isinstance(input_path, list):
            files = [Path(f) for f in input_path]
        else:
            input_path = Path(input_path)
            if input_path.is_dir():
                files = list(input_path.glob('*.pdf'))
            else:
                progress_queue.put({"type": "log", "tag": "error", "msg": f"Invalid input path: {input_path}"})
                progress_queue.put({"type": "finish", "status": "Error"})
                return
                
        if not files:
            progress_queue.put({"type": "log", "tag": "warning", "msg": "No PDF files found to process."})
            progress_queue.put({"type": "finish", "status": "Complete"})
            return
            
        progress_queue.put({"type": "log", "tag": "info", "msg": f"Found {len(files)} PDF files to process."})
        
        # Process each PDF file
        results = {}
        for i, path in enumerate(files):
            # Check for cancellation or pause
            if cancel_event.is_set():
                progress_queue.put({"type": "log", "tag": "warning", "msg": "Processing cancelled by user."})
                progress_queue.put({"type": "finish", "status": "Cancelled"})
                return
                
            if pause_event and pause_event.is_set():
                progress_queue.put({"type": "status", "msg": "Paused", "led": "Paused"})
                while pause_event.is_set() and not cancel_event.is_set():
                    time.sleep(0.5)
                    
            # Run garbage collection periodically
            if i > 0 and i % 20 == 0:
                cleanup_memory()
                
            # Update progress
            progress_queue.put({"type": "progress", "current": i + 1, "total": len(files)})
            
            # Process the file
            res = process_single_pdf(path, progress_queue, ignore_cache=is_rerun)
            if res:
                results[res["filename"]] = res

        # Final cancellation check
        if cancel_event.is_set():
            progress_queue.put({"type": "finish", "status": "Cancelled"})
            return

        # Update the Excel file with the results
        progress_queue.put({"type": "status", "msg": "Updating Excel...", "led": "Saving"})
        try:
            workbook = openpyxl.load_workbook(cloned_path)
            sheet = workbook.active
            headers = [c.value if c.value is not None else "" for c in sheet[1]]
            
            # Add Processing Status column if it doesn't exist
            status_col_name = "Processing Status"
            if status_col_name not in headers:
                sheet.cell(row=1, column=len(headers) + 1).value = status_col_name
                headers.append(status_col_name)
                
            # Get column indices
            cols = {}
            for header_name in [META_COLUMN_NAME, "Author", "Short description", status_col_name]:
                if header_name in headers:
                    cols[header_name] = headers.index(header_name) + 1
                else:
                    progress_queue.put({"type": "log", "tag": "warning", 
                                        "msg": f"Column '{header_name}' not found in Excel file."})
            
            # Update existing rows
            updates_made = 0
            for row in sheet.iter_rows(min_row=2):
                if "Short description" in cols:
                    desc = str(row[cols["Short description"]-1].value or "")
                    for filename, data in results.items():
                        if Path(filename).stem in desc:
                            # Update meta column if it exists
                            if META_COLUMN_NAME in cols and data.get("models"):
                                row[cols[META_COLUMN_NAME]-1].value = data["models"]
                                
                            # Update author column if it exists
                            if "Author" in cols and data.get("author"):
                                row[cols["Author"]-1].value = data["author"]
                                
                            # Update status column if it exists
                            if status_col_name in cols:
                                status_str = f"{data['status']}{' (OCR)' if data['ocr_used'] else ''}"
                                row[cols[status_col_name]-1].value = status_str
                                
                            updates_made += 1
                            break
            
            # Apply formatting based on status
            progress_queue.put({"type": "status", "msg": "Applying formatting...", "led": "Saving"})
            fills = {
                "Pass": PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"),
                "Fail": PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"),
                "Needs Review": PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid"),
                "OCR": PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
            }
            
            # Apply status-based cell coloring
            if status_col_name in cols:
                for row in sheet.iter_rows(min_row=2):
                    status_cell = row[cols[status_col_name]-1]
                    status_val = str(status_cell.value or "")
                    fill_key = status_val.replace(" (OCR)", "").strip()
                    fill = fills.get(fill_key)
                    
                    if fill:
                        # Apply the status color to the entire row
                        for cell in row:
                            cell.alignment = Alignment(wrap_text=True, vertical="top")
                            cell.fill = fill
                            
                        # If OCR was used, override the status cell color
                        if "(OCR)" in status_val:
                            status_cell.fill = fills["OCR"]
            
            # Adjust column widths for better readability
            for i, col in enumerate(sheet.columns, 1):
                max_len = max((len(str(c.value or "")) for c in col), default=0)
                sheet.column_dimensions[get_column_letter(i)].width = min(max_len + 2, 60)

            # Save the updated workbook
            workbook.save(cloned_path)
            progress_queue.put({"type": "log", "tag": "success", 
                               f"msg": f"Updated {updates_made} rows in Excel file."})
            progress_queue.put({"type": "result_path", "path": str(cloned_path)})
            progress_queue.put({"type": "finish", "status": "Complete"})

        except InvalidFileException as e:
            progress_queue.put({"type": "log", "tag": "error", 
                                "msg": f"Excel file format error: {e}. The file might be password protected."})
            progress_queue.put({"type": "finish", "status": "Error"})
            
        except Exception as e:
            progress_queue.put({"type": "log", "tag": "error", "msg": f"Error updating Excel: {e}"})
            progress_queue.put({"type": "finish", "status": "Error"})

    except Exception as e:
        progress_queue.put({"type": "log", "tag": "error", "msg": f"Critical error: {e}"})
        progress_queue.put({"type": "finish", "status": f"Error: {e}"})


def _execute_job(job_info, log_fn, status_fn, finish_fn, progress_fn, review_fn, cancel_check):
    """Internal helper to execute a processing job. Simplified for tests."""
    q = Queue()
    cancel_event = threading.Event()
    thread = threading.Thread(
        target=run_processing_job,
        args=(job_info, q, cancel_event, None),
        daemon=True,
    )
    thread.start()
    thread.join(0)


def process_folder(folder, excel_path, log_fn, status_fn, finish_fn, progress_fn, cancel_check):
    """Validate folder and start a processing job."""
    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(folder)

    job = {
        "input_path": folder_path,
        "excel_path": Path(excel_path),
    }
    _execute_job(job, log_fn, status_fn, finish_fn, progress_fn, cancel_check)


def process_zip_archive(zip_path, excel_path, log_fn, status_fn, finish_fn, progress_fn, cancel_check):
    """Extract a zip archive then process the contained PDFs."""
    with zipfile.ZipFile(zip_path) as zf:
        extract_dir = Path(zip_path).with_suffix("")
        zf.extractall(extract_dir)

    process_folder(extract_dir, excel_path, log_fn, status_fn, finish_fn, progress_fn, cancel_check)

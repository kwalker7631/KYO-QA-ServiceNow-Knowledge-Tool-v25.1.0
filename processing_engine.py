# processing_engine.py
import shutil
import time
import json
import fitz
import threading
from queue import Queue
from pathlib import Path
from datetime import datetime
import tempfile
try:  # pragma: no cover - optional dependency
    import openpyxl
    from openpyxl.styles import PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except Exception:  # pragma: no cover - if openpyxl missing use stubs
    import types, sys
    openpyxl = types.ModuleType("openpyxl")
    # Minimal styles stub
    styles = types.ModuleType("styles")
    PatternFill = Alignment = Font = type("_S", (), {})
    styles.PatternFill = PatternFill
    styles.Alignment = Alignment
    styles.Font = Font
    openpyxl.styles = styles
    # Formatting stub
    formatting = types.ModuleType("formatting")
    rule_mod = types.ModuleType("rule")
    rule_mod.FormulaRule = type("FormulaRule", (), {})
    formatting.rule = rule_mod
    openpyxl.formatting = formatting
    # Utils stub
    utils = types.ModuleType("utils")
    def get_column_letter(idx):
        return str(idx)
    utils.get_column_letter = get_column_letter
    openpyxl.utils = utils
    # Workbook helpers
    class _WB:
        def __init__(self, *a, **k):
            self.active = types.SimpleNamespace()
    openpyxl.Workbook = _WB
    def load_workbook(*a, **k):
        return _WB()
    openpyxl.load_workbook = load_workbook
    sys.modules.setdefault("openpyxl", openpyxl)
    sys.modules.setdefault("openpyxl.styles", styles)
    sys.modules.setdefault("openpyxl.formatting", formatting)
    sys.modules.setdefault("openpyxl.formatting.rule", rule_mod)
    sys.modules.setdefault("openpyxl.utils", utils)
from config import (META_COLUMN_NAME, OUTPUT_DIR, PDF_TXT_DIR, HEADER_MAPPING)
from custom_exceptions import FileLockError
from data_harvesters import harvest_all_data
from file_utils import is_file_locked
from ocr_utils import extract_text_from_pdf, _is_ocr_needed
from ai_extractor import ai_extract
from logging_utils import create_success_log, create_failure_log

CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_path(pdf_path: Path) -> Path:
    """Generates a unique cache file path based on the PDF's name and size."""
    try:
        pdf_size = pdf_path.stat().st_size
        return CACHE_DIR / f"{pdf_path.stem}_{pdf_size}.json"
    except FileNotFoundError:
        return CACHE_DIR / f"{pdf_path.stem}_unknown.json"

def clear_review_folder():
    """Deletes all .txt files in the PDF_TXT directory."""
    if PDF_TXT_DIR.exists():
        for f in PDF_TXT_DIR.glob("*.txt"):
            try:
                f.unlink()
            except OSError as e:
                print(f"Error deleting review file {f}: {e}")


def map_to_servicenow_format(data: dict, filename: str) -> dict:
    """Convert harvested data into a ServiceNow-friendly dictionary."""
    mapped = {header: "" for header in HEADER_MAPPING.values()}

    mapped[HEADER_MAPPING["file_name"]] = filename
    mapped[HEADER_MAPPING["short_description"]] = (
        data.get("subject") or filename
    )
    mapped[HEADER_MAPPING["models"]] = data.get("models", "")
    mapped[HEADER_MAPPING["author"]] = data.get("author", "")
    if data.get("published_date"):
        mapped[HEADER_MAPPING["scheduled_publish_date"]] = data["published_date"]

    mapped[HEADER_MAPPING["processing_status"]] = (
        "Needs Review" if data.get("needs_review") else "Pass"
    )
    return mapped


def process_folder(folder_path: str, kb_filepath: str, progress_cb=None, status_cb=None, *_, **__):
    """Thin wrapper that delegates to ``run_processing_job`` for a folder."""
    job = {"excel_path": kb_filepath, "input_path": folder_path}
    run_processing_job(job, Queue(), type("C", (), {"is_set": lambda self: False})())


def process_zip_archive(zip_path: str, kb_filepath: str, progress_cb=None, status_cb=None, *_, **__):
    """Thin wrapper that delegates to ``run_processing_job`` for a zip archive."""
    job = {"excel_path": kb_filepath, "input_path": zip_path}
    run_processing_job(job, Queue(), type("C", (), {"is_set": lambda self: False})())

def process_single_pdf(pdf_path: Path, progress_queue: Queue, ignore_cache: bool = False) -> dict:
    """Processes a single PDF, with more robust caching."""
    filename = pdf_path.name
    cache_path = get_cache_path(pdf_path)

    # Step 1: Check for a valid cached result
    if not ignore_cache and cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            #==============================================================
            # --- MODIFICATION: More robust handling of cached review files ---
            #==============================================================
            if cached_data.get("status") == "Needs Review":
                review_info = cached_data.get("review_info")
                # Check if the cache is stale (missing the text content)
                if review_info and review_info.get("text_content"):
                    # Re-create the txt file from cached text if it doesn't exist
                    if not Path(review_info["txt_path"]).exists():
                        with open(review_info["txt_path"], 'w', encoding='utf-8') as f:
                            f.write(review_info["text_content"])
                    progress_queue.put({"type": "review_item", "data": review_info})
                else:
                    # If cache is stale, we must re-process. Returning None will trigger it.
                    progress_queue.put({"type": "log", "tag": "warning", "msg": f"Stale cache for {filename}, re-processing..."})
                    return None # Returning None signals to re-process
            #==============================================================
            # --- END OF MODIFICATION ---
            #==============================================================

            progress_queue.put({"type": "log", "tag": "info", "msg": f"Loaded from cache: {filename}"})
            progress_queue.put({"type": "file_complete", "status": cached_data.get("status")})
            if cached_data.get("ocr_used"):
                 progress_queue.put({"type": "increment_counter", "counter": "ocr"})
            return cached_data
        except (json.JSONDecodeError, KeyError):
             progress_queue.put({"type": "log", "tag": "warning", "msg": f"Corrupt cache for {filename}. Reprocessing..."})

    # Step 2: If no valid cache, perform full processing
    final_status, review_info = "", None
    progress_queue.put({"type": "status", "msg": filename, "led": "Queued"})
    
    ocr_required = _is_ocr_needed(pdf_path)
    if ocr_required:
        progress_queue.put({"type": "status", "msg": filename, "led": "OCR"})
        progress_queue.put({"type": "increment_counter", "counter": "ocr"})
    
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text or not extracted_text.strip():
        final_status = "Fail"
        result = {"filename": filename, "models": "Error: Text Extraction Failed", "author": "", "status": final_status, "ocr_used": ocr_required}
    else:
        progress_queue.put({"type": "status", "msg": filename, "led": "AI"})
        data = harvest_all_data(extracted_text, filename)
        models_found = data.get("models")

        if not models_found or models_found == "Not Found":
            final_status = "Needs Review"
            review_txt_path = PDF_TXT_DIR / f"{filename}.txt"
            header = f"--- Original Filename: {filename} ---\n--- QA Number Found: {data.get('full_qa_number', 'None')} ---\n\n"
            file_content_for_review = header + extracted_text
            try:
                with open(review_txt_path, 'w', encoding='utf-8') as f:
                    f.write(file_content_for_review)
            except OSError as e:
                progress_queue.put({
                    "type": "log",
                    "tag": "error",
                    "msg": f"Failed to write review file for {filename}: {e}"
                })
                review_info = None
            else:
                review_info = {
                    "filename": filename,
                    "reason": "No models found",
                    "txt_path": str(review_txt_path),
                    "pdf_path": str(pdf_path),
                    "text_content": file_content_for_review,
                }
                progress_queue.put({"type": "review_item", "data": review_info})
            data["models"] = "Review Needed"
        else:
            final_status = "Pass"
            progress_queue.put({"type": "log", "tag": "success", "msg": f"Finished: {filename}. Found: {models_found}"})
        
        result = {"filename": filename, **data, "status": final_status, "ocr_used": ocr_required, "review_info": review_info}

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)

    progress_queue.put({"type": "file_complete", "status": final_status})
    return result


def run_processing_job(job_info: dict, progress_queue: Queue, cancel_event):
    excel_path_str = job_info["excel_path"]
    input_path = job_info["input_path"]
    is_rerun = job_info.get("is_rerun", False)
    pause_event = job_info.get("pause_event")

    try:
        progress_queue.put({"type": "log", "tag": "info", "msg": "Processing job started."})

        if is_rerun:
            progress_queue.put({"type": "status", "msg": "Cleaning review folder for re-run...", "led": "Setup"})
            clear_review_folder()
            cloned_excel_path = Path(excel_path_str)
            progress_queue.put({"type": "log", "tag": "info", "msg": f"Re-running process on: {cloned_excel_path.name}"})
        else:
            base_excel_path = Path(excel_path_str)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            cloned_filename = f"cloned_{base_excel_path.stem}_{timestamp}{base_excel_path.suffix}"
            cloned_excel_path = OUTPUT_DIR / cloned_filename
            progress_queue.put({"type": "status", "msg": f"Cloning '{base_excel_path.name}'...", "led": "Setup"})
            if is_file_locked(base_excel_path): raise FileLockError(f"Input Excel file is locked: {base_excel_path.name}")
            shutil.copy(base_excel_path, cloned_excel_path)
            progress_queue.put({"type": "log", "tag": "success", "msg": f"Cloned file saved to: {cloned_excel_path}"})

        files_to_process = [Path(f) for f in input_path] if isinstance(input_path, list) else [f for f in Path(input_path).iterdir() if f.suffix.lower() in ['.pdf', '.zip']]
        
        results_map = {}
        for i, file_path in enumerate(files_to_process):
            if pause_event and pause_event.is_set():
                progress_queue.put({"type": "status", "msg": "Paused. Waiting to resume...", "led": "Paused"})
                while pause_event.is_set():
                    if cancel_event.is_set(): break
                    time.sleep(0.5)

            if cancel_event.is_set(): break
            progress_queue.put({"type": "progress", "current": i + 1, "total": len(files_to_process)})
            if file_path.suffix.lower() == '.pdf':
                result = process_single_pdf(file_path, progress_queue, ignore_cache=is_rerun)
                # If cache was stale, process_single_pdf returns None, so we re-process.
                if result is None:
                    result = process_single_pdf(file_path, progress_queue, ignore_cache=True)
                results_map[result["filename"]] = result
        
        if cancel_event.is_set():
            progress_queue.put({"type": "finish", "status": "Cancelled"}); return

        progress_queue.put({"type": "status", "msg": f"Updating '{cloned_excel_path.name}'...", "led": "Saving"})
        
        workbook = openpyxl.load_workbook(cloned_excel_path)
        sheet = workbook.active
        headers = [cell.value for cell in sheet[1]]
        
        if "Processing Status" not in headers:
            sheet.cell(row=1, column=len(headers) + 1).value = "Processing Status"
            headers.append("Processing Status")
            
        try:
            desc_col_idx, meta_col_idx, author_col_idx, status_col_idx = [headers.index(h) + 1 for h in ["Short description", META_COLUMN_NAME, "Author", "Processing Status"]]
        except ValueError as e:
            raise ValueError(f"Could not find required column in Excel: {e}")

        updates_made, appends_made = 0, 0
        pdfs_found_in_sheet = set()
        
        for row_idx in range(2, sheet.max_row + 1):
            description = str(sheet.cell(row=row_idx, column=desc_col_idx).value)
            for filename, data in results_map.items():
                if Path(filename).stem in description:
                    meta_cell = sheet.cell(row=row_idx, column=meta_col_idx)
                    author_cell = sheet.cell(row=row_idx, column=author_col_idx)
                    status_cell = sheet.cell(row=row_idx, column=status_col_idx)
                    meta_cell.value = data["models"]
                    updates_made += 1
                    author_cell.value = data.get("author", "")
                    status_cell.value = f"{data['status']}{' (OCR)' if data['ocr_used'] else ''}"
                    pdfs_found_in_sheet.add(filename)
                    break

        pdfs_to_add = [data for filename, data in results_map.items() if filename not in pdfs_found_in_sheet]
        if pdfs_to_add:
            for data in pdfs_to_add:
                new_row = [""] * len(headers)
                new_row[desc_col_idx - 1] = data.get("short_description", data["filename"])
                new_row[meta_col_idx - 1] = data["models"]
                new_row[author_col_idx - 1] = data.get("author", "")
                new_row[status_col_idx -1] = f"{data['status']}{' (OCR)' if data['ocr_used'] else ''}"
                sheet.append(new_row)
                appends_made += 1

        progress_queue.put({"type": "log", "tag": "info", "msg": f"{updates_made} existing rows updated, {appends_made} new rows appended."})
        
        progress_queue.put({"type": "status", "msg": "Applying final formatting...", "led": "Saving"})
        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        blue_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
        wrap_alignment = Alignment(wrap_text=True, vertical='top')
        
        for row in sheet.iter_rows(min_row=2):
            status_val = str(row[status_col_idx-1].value)
            fill_to_apply = None
            if "Pass" in status_val: fill_to_apply = green_fill
            elif "Fail" in status_val: fill_to_apply = red_fill
            elif "Review" in status_val: fill_to_apply = yellow_fill
            for cell in row:
                if fill_to_apply: cell.fill = fill_to_apply
                cell.alignment = wrap_alignment
            if "OCR" in status_val: row[status_col_idx -1].fill = blue_fill
        
        for i, column_cells in enumerate(sheet.columns):
            max_length = 0
            column = get_column_letter(i + 1)
            for cell in column_cells:
                try:
                    if len(str(cell.value)) > max_length: max_length = len(str(cell.value))
                except: pass
            adjusted_width = (max_length + 2) if max_length < 50 else 50
            sheet.column_dimensions[column].width = adjusted_width

        progress_queue.put({"type": "status", "msg": "Saving final XLSX file... Please be patient.", "led": "Saving"})
        workbook.save(cloned_excel_path)
        progress_queue.put({"type": "log", "tag": "success", "msg": f"Successfully saved all changes to: {cloned_excel_path.name}"})

        progress_queue.put({"type": "result_path", "path": str(cloned_excel_path)})
        progress_queue.put({"type": "finish", "status": "Complete"})

    except Exception as e:
        error_message = f"A critical error occurred: {e}"
        progress_queue.put({"type": "log", "tag": "error", "msg": error_message})
        progress_queue.put({"type": "finish", "status": f"Error: {e}"})

def process_folder(folder_path, kb_filepath, *_, **__):
    """Legacy wrapper that processes a directory of PDFs."""
    job = {"excel_path": kb_filepath, "input_path": folder_path}
    run_processing_job(job, Queue(), threading.Event())


def process_zip_archive(zip_path, kb_filepath, *_, **__):
    """Legacy wrapper that processes a ZIP of PDFs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmpdir)
        job = {"excel_path": kb_filepath, "input_path": tmpdir}
        run_processing_job(job, Queue(), threading.Event())


def _main_processing_loop(files_to_process, kb_filepath, progress_cb, status_cb, ocr_cb, review_cb, cancel_event):
    """Simplified loop retained for backward compatibility in tests."""
    updated_count, failed_count = 0, 0
    for i, file_path in enumerate(files_to_process):
        if cancel_event.is_set():
            break

        progress_cb(f"Processing {i + 1}/{len(files_to_process)}: {file_path.name}")
        status_cb("file", f"Opening {file_path.name}...")
        try:
            needs_ocr = _is_ocr_needed(file_path)
            if needs_ocr:
                status_cb("OCR", f"Performing OCR on {file_path.name}...")
            text = extract_text_from_pdf(file_path)
            if needs_ocr:
                ocr_cb()
            if not text:
                status_cb("FAIL", f"Failed: Could not extract text from {file_path.name}")
                failed_count += 1
                continue

            status_cb("AI", f"Analyzing content of {file_path.name}...")
            extracted = ai_extract(text, file_path)
            if extracted.get("needs_review"):
                status_cb("NEEDS_REVIEW", f"{file_path.name} flagged for manual review.")
                review_cb()
            else:
                status_cb("SUCCESS", f"Successfully extracted data from {file_path.name}.")

            updated_count += 1
        except Exception:
            status_cb("FAIL", f"Critical error on {file_path.name}")
            failed_count += 1

    if updated_count > 0:
        create_success_log(f"{updated_count} record(s) updated, {failed_count} file(s) failed.")
    else:
        create_failure_log(f"{updated_count} record(s) updated, {failed_count} file(s) failed.", "No updates")

    return kb_filepath, updated_count, failed_count
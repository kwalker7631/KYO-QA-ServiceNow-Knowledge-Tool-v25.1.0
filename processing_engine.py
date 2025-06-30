# processing_engine.py
import shutil
import time
import zipfile
import json
from queue import Queue
from pathlib import Path
from datetime import datetime
import sys
import types
try:
    import openpyxl
    from openpyxl.styles import PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except Exception:  # pragma: no cover - fallback for test envs without openpyxl
    openpyxl = types.ModuleType('openpyxl')
    PatternFill = Alignment = object
    def get_column_letter(idx):
        return str(idx)
    openpyxl.styles = types.SimpleNamespace(PatternFill=PatternFill, Alignment=Alignment)
    openpyxl.utils = types.SimpleNamespace(get_column_letter=get_column_letter)
    sys.modules.setdefault('openpyxl', openpyxl)

try:
    import pandas as pd
except Exception:  # pragma: no cover - fallback when pandas missing
    pd = types.ModuleType('pandas')

from ai_extractor import ai_extract

from config import (META_COLUMN_NAME, OUTPUT_DIR, PDF_TXT_DIR)
from custom_exceptions import FileLockError
from data_harvesters import harvest_all_data
from file_utils import (cleanup_temp_files, get_temp_dir, is_file_locked)
from ocr_utils import extract_text_from_pdf, _is_ocr_needed

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
            with open(review_txt_path, 'w', encoding='utf-8') as f:
                f.write(file_content_for_review)
            review_info = {"filename": filename, "reason": "No models found", "txt_path": str(review_txt_path), "pdf_path": str(pdf_path), "text_content": file_content_for_review}
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
                progress_queue.put({"type": "status", "msg": f"Paused. Waiting to resume...", "led": "Paused"})
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
                    if meta_cell.value is None or str(meta_cell.value).strip() in ["", "Review Needed"]:
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


def _legacy_main_processing_loop(files_to_process, kb_filepath, progress_cb, status_cb, ocr_cb, review_cb, cancel_event):
    """Simplified processing loop used when openpyxl is unavailable."""
    if is_file_locked(Path(kb_filepath)):
        raise FileLockError(f"Knowledge Base file is locked: {kb_filepath}")

    df = pd.read_excel(kb_filepath, engine='openpyxl')
    updated_count, failed_count = 0, 0
    for i, file_path in enumerate(files_to_process):
        if cancel_event.is_set():
            break

        progress_cb(f"Processing {i+1}/{len(files_to_process)}: {file_path.name}")
        status_cb("file", f"Opening {file_path.name}...")

        try:
            target_rows = df.index[df['Description'] == file_path.name].tolist()
            if not target_rows:
                continue

            needs_ocr = _is_ocr_needed(file_path)
            if needs_ocr:
                status_cb("OCR", f"Performing OCR on {file_path.name}...")

            text = extract_text_from_pdf(file_path, ocr_cb if needs_ocr else None)
            if not text:
                status_cb("FAIL", f"Failed: Could not extract text from {file_path.name}")
                failed_count += 1
                continue

            status_cb("AI", f"Analyzing content of {file_path.name}...")
            extracted_data = ai_extract(text, file_path)

            if extracted_data.get("needs_review"):
                status_cb("NEEDS_REVIEW", f"{file_path.name} flagged for manual review.")
                review_cb()

            row_index = target_rows[0]
            formatted_record = map_to_servicenow_format(extracted_data, file_path.name)
            for header_name, value in formatted_record.items():
                if header_name in df.columns:
                    if getattr(pd, 'isna', lambda x: x is None)(df.at[row_index, header_name]) or str(df.at[row_index, header_name]).strip() == '':
                        df.at[row_index, header_name] = value
            updated_count += 1
        except Exception:
            status_cb("FAIL", f"Critical error on {file_path.name}")
            failed_count += 1

    if updated_count > 0:
        df.to_excel(kb_filepath, index=False, engine='openpyxl')
        create_success_log(f"{updated_count} record(s) updated, {failed_count} file(s) failed.")
    else:
        create_failure_log(f"{updated_count} record(s) updated, {failed_count} file(s) failed.", "No updates")

    return kb_filepath, updated_count, failed_count


def process_folder(folder_path, kb_filepath, progress_cb, status_cb, ocr_cb, review_cb, cancel_event):
    """Public wrapper to process a folder of PDFs."""
    files = [p for p in Path(folder_path).iterdir() if p.suffix.lower() in ['.pdf', '.zip']]
    if hasattr(openpyxl, 'load_workbook'):
        job = {"excel_path": kb_filepath, "input_path": folder_path}
        q = Queue()
        run_processing_job(job, q, cancel_event)
        while not q.empty():
            item = q.get()
            if item.get("type") == "increment_counter" and item.get("counter") == "ocr":
                ocr_cb()
            if item.get("type") == "review_item":
                review_cb()
    else:
        return _legacy_main_processing_loop(files, kb_filepath, progress_cb, status_cb, ocr_cb, review_cb, cancel_event)


def process_zip_archive(zip_path, kb_filepath, progress_cb, status_cb, ocr_cb, review_cb, cancel_event):
    """Process PDFs from within a zip archive."""
    temp_dir = get_temp_dir()
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            pdf_names = [f for f in zip_ref.namelist() if f.lower().endswith('.pdf') and not f.startswith('__MACOSX')]
            if not pdf_names:
                return kb_filepath, 0, 0
            zip_ref.extractall(temp_dir, members=pdf_names)
            files = [temp_dir / name for name in pdf_names]
            if hasattr(openpyxl, 'load_workbook'):
                job = {"excel_path": kb_filepath, "input_path": files}
                q = Queue()
                run_processing_job(job, q, cancel_event)
                while not q.empty():
                    item = q.get()
                    if item.get("type") == "increment_counter" and item.get("counter") == "ocr":
                        ocr_cb()
                    if item.get("type") == "review_item":
                        review_cb()
            else:
                return _legacy_main_processing_loop(files, kb_filepath, progress_cb, status_cb, ocr_cb, review_cb, cancel_event)
    finally:
        cleanup_temp_files(temp_dir)


def map_to_servicenow_format(extracted_data, filename):
    """Map extracted data keys to the ServiceNow Excel headers."""
    from config import HEADER_MAPPING
    record = {header: "" for header in HEADER_MAPPING.values()}
    record[HEADER_MAPPING["file_name"]] = filename
    needs_review = bool(extracted_data.get("needs_review", False))
    record[HEADER_MAPPING["needs_review"]] = needs_review
    record[HEADER_MAPPING["processing_status"]] = "Needs Review" if needs_review else "Success"
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


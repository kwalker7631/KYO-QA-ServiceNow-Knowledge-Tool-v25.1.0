# processing_engine.py
# Compatible version that works with existing data_harvesters.py
import shutil
import time
import zipfile
import json
from queue import Queue
from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.styles import PatternFill, Alignment
from openpyxl.utils import get_column_letter

# Import from our other modules
from config import META_COLUMN_NAME, OUTPUT_DIR, PDF_TXT_DIR
from custom_exceptions import FileLockError
from data_harvesters import bulletproof_extraction  # Use the function that exists
from file_utils import cleanup_temp_files, get_temp_dir, is_file_locked
from ocr_utils import extract_text_from_pdf, _is_ocr_needed
from recycle_utils import apply_recycles

# Cache directory for storing processed results
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

def clear_cache_folder():
    """Deletes cached JSON results to force reprocessing."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            try:
                f.unlink()
            except OSError as e:
                print(f"Error deleting cache file {f}: {e}")

def process_single_pdf(pdf_path: Path, progress_queue: Queue, ignore_cache: bool = False) -> dict:
    """Processes a single PDF, now with caching capabilities."""
    filename = pdf_path.name
    cache_path = get_cache_path(pdf_path)

    # Step 1: Check for a cached result
    if not ignore_cache and cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            progress_queue.put({"type": "log", "tag": "info", "msg": f"Loaded from cache: {filename}"})
            
            if cached_data.get("status") == "Needs Review":
                progress_queue.put({"type": "review_item", "data": cached_data.get("review_info")})
            progress_queue.put({"type": "file_complete", "status": cached_data.get("status")})
            if cached_data.get("ocr_used"):
                 progress_queue.put({"type": "increment_counter", "counter": "ocr"})
            return cached_data
        except (json.JSONDecodeError, KeyError):
             progress_queue.put({"type": "log", "tag": "warning", "msg": f"Corrupt cache for {filename}. Reprocessing..."})

    # Step 2: If no cache, perform full processing
    final_status = ""
    review_info = None
    progress_queue.put({"type": "status", "msg": filename, "led": "Queued"})
    
    ocr_required = _is_ocr_needed(pdf_path)
    if ocr_required:
        progress_queue.put({"type": "status", "msg": filename, "led": "OCR"})
        progress_queue.put({"type": "increment_counter", "counter": "ocr"})
    
    extracted_text = extract_text_from_pdf(pdf_path)
    # Apply recycle rules before harvesting
    extracted_text = apply_recycles(extracted_text)
    if not extracted_text or not extracted_text.strip():
        final_status = "Fail"
        result = {"filename": filename, "models": "Error: Text Extraction Failed", "author": "", "status": final_status, "ocr_used": ocr_required}
    else:
        progress_queue.put({"type": "status", "msg": filename, "led": "AI"})
        # Use bulletproof_extraction function that exists in your data_harvesters.py
        data = bulletproof_extraction(extracted_text, filename)
        models_found = data.get("models")

        if not models_found or models_found == "Not Found":
            final_status = "Needs Review"
            review_txt_path = PDF_TXT_DIR / f"{filename}.txt"
            header = f"--- Original Filename: {filename} ---\n--- QA Number Found: {data.get('full_qa_number', 'None')} ---\n\n"
            with open(review_txt_path, 'w', encoding='utf-8') as f:
                f.write(header + extracted_text)
            review_info = {"filename": filename, "reason": "No models found", "txt_path": str(review_txt_path), "pdf_path": str(pdf_path)}
            progress_queue.put({"type": "review_item", "data": review_info})
            data["models"] = "Review Needed"
        else:
            final_status = "Pass"
            progress_queue.put({"type": "log", "tag": "success", "msg": f"Finished: {filename}. Found: {models_found}"})
        
        result = {"filename": filename, **data, "status": final_status, "ocr_used": ocr_required, "review_info": review_info}

    # Step 3: Save the result to cache before returning
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4)

    progress_queue.put({"type": "file_complete", "status": final_status})
    return result

def run_processing_job(job_info: dict, progress_queue: Queue, cancel_event):
    """Main processing job function - this is what the main app calls."""
    excel_path_str = job_info["excel_path"]
    input_path = job_info["input_path"]
    is_rerun = job_info.get("is_rerun", False)
    pause_event = job_info.get("pause_event")

    try:
        progress_queue.put({"type": "log", "tag": "info", "msg": "Processing job started."})

        if is_rerun:
            cloned_excel_path = Path(excel_path_str)
            progress_queue.put({"type": "log", "tag": "info", "msg": f"Re-running process on: {cloned_excel_path.name}"})
            clear_review_folder()
            clear_cache_folder()
        else:
            progress_queue.put({"type": "status", "msg": "Cleaning review folder...", "led": "Setup"})
            clear_review_folder()
            base_excel_path = Path(excel_path_str)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            cloned_filename = f"cloned_{base_excel_path.stem}_{timestamp}{base_excel_path.suffix}"
            cloned_excel_path = OUTPUT_DIR / cloned_filename
            progress_queue.put({"type": "status", "msg": f"Cloning '{base_excel_path.name}'...", "led": "Setup"})
            if is_file_locked(base_excel_path): 
                raise FileLockError(f"Input Excel file is locked: {base_excel_path.name}")
            shutil.copy(base_excel_path, cloned_excel_path)
            progress_queue.put({"type": "log", "tag": "success", "msg": f"Cloned file saved to: {cloned_excel_path}"})

        # Determine files to process
        files_to_process = []
        if isinstance(input_path, list):
            files_to_process = [Path(f) for f in input_path]
        else:
            input_path = Path(input_path)
            files_to_process = [
                f for f in input_path.iterdir()
                if f.suffix.lower() in ['.pdf', '.zip'] and PDF_TXT_DIR not in f.parents
            ]
        
        results_map = {}
        for i, file_path in enumerate(files_to_process):
            # Handle pause functionality
            if pause_event and pause_event.is_set():
                progress_queue.put({"type": "status", "msg": f"Paused. Waiting to resume...", "led": "Paused"})
                while pause_event.is_set():
                    if cancel_event.is_set(): 
                        break
                    time.sleep(0.5)

            # Handle cancellation
            if cancel_event.is_set(): 
                break
                
            progress_queue.put({"type": "progress", "current": i + 1, "total": len(files_to_process)})
            
            if file_path.suffix.lower() == '.pdf':
                result = process_single_pdf(file_path, progress_queue, ignore_cache=is_rerun)
                results_map[result["filename"]] = result
        
        if cancel_event.is_set():
            progress_queue.put({"type": "finish", "status": "Cancelled"})
            return

        # Update Excel file
        progress_queue.put({"type": "status", "msg": f"Updating '{cloned_excel_path.name}'...", "led": "Saving"})
        
        workbook = openpyxl.load_workbook(cloned_excel_path)
        sheet = workbook.active
        headers = [cell.value for cell in sheet[1]]
        
        # Add Processing Status column if it doesn't exist
        if "Processing Status" not in headers:
            sheet.cell(row=1, column=len(headers) + 1).value = "Processing Status"
            headers.append("Processing Status")
            
        try:
            desc_col_idx = headers.index("Short description") + 1
            meta_col_idx = headers.index(META_COLUMN_NAME) + 1
            author_col_idx = headers.index("Author") + 1
            status_col_idx = headers.index("Processing Status") + 1
        except ValueError as e:
            raise ValueError(f"Could not find required column in Excel: {e}")

        updates_made = 0
        appends_made = 0
        pdfs_found_in_sheet = set()
        
        # Update existing rows
        for row_idx in range(2, sheet.max_row + 1):
            description = str(sheet.cell(row=row_idx, column=desc_col_idx).value or "")
            for filename, data in results_map.items():
                if Path(filename).stem in description:
                    sheet.cell(row=row_idx, column=meta_col_idx).value = data["models"]
                    sheet.cell(row=row_idx, column=author_col_idx).value = data.get("author", "")
                    sheet.cell(row=row_idx, column=status_col_idx).value = f"{data['status']}{' (OCR)' if data['ocr_used'] else ''}"
                    updates_made += 1
                    pdfs_found_in_sheet.add(filename)
                    break

        # Add new rows for PDFs not found in sheet
        pdfs_to_add = [data for filename, data in results_map.items() if filename not in pdfs_found_in_sheet]
        if pdfs_to_add:
            for data in pdfs_to_add:
                new_row = [""] * len(headers)
                new_row[desc_col_idx - 1] = data.get("short_description", data["filename"])
                new_row[meta_col_idx - 1] = data["models"]
                new_row[author_col_idx - 1] = data.get("author", "")
                new_row[status_col_idx - 1] = f"{data['status']}{' (OCR)' if data['ocr_used'] else ''}"
                sheet.append(new_row)
                appends_made += 1

        progress_queue.put({"type": "log", "tag": "info", "msg": f"{updates_made} existing rows updated, {appends_made} new rows appended."})
        
        # Apply formatting
        progress_queue.put({"type": "status", "msg": "Applying final formatting...", "led": "Saving"})
        green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        yellow_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
        blue_fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
        wrap_alignment = Alignment(wrap_text=True, vertical='top')
        
        for row in sheet.iter_rows(min_row=2):
            status_val = str(row[status_col_idx-1].value or "")
            fill_to_apply = None
            if "Pass" in status_val: 
                fill_to_apply = green_fill
            elif "Fail" in status_val: 
                fill_to_apply = red_fill
            elif "Review" in status_val: 
                fill_to_apply = yellow_fill
                
            for cell in row:
                if fill_to_apply: 
                    cell.fill = fill_to_apply
                cell.alignment = wrap_alignment
                
            if "OCR" in status_val: 
                row[status_col_idx - 1].fill = blue_fill
        
        # Adjust column widths
        for i, column_cells in enumerate(sheet.columns):
            max_length = 0
            column = get_column_letter(i + 1)
            for cell in column_cells:
                try:
                    if len(str(cell.value or "")) > max_length: 
                        max_length = len(str(cell.value))
                except: 
                    pass
            adjusted_width = (max_length + 2) if max_length < 50 else 50
            sheet.column_dimensions[column].width = adjusted_width

        # Save the workbook
        progress_queue.put({"type": "status", "msg": "Saving final XLSX file... Please be patient.", "led": "Saving"})
        workbook.save(cloned_excel_path)
        progress_queue.put({"type": "log", "tag": "success", "msg": f"Successfully saved all changes to: {cloned_excel_path.name}"})

        progress_queue.put({"type": "result_path", "path": str(cloned_excel_path)})
        progress_queue.put({"type": "finish", "status": "Complete"})

    except Exception as e:
        error_message = f"A critical error occurred: {e}"
        progress_queue.put({"type": "log", "tag": "error", "msg": error_message})
        progress_queue.put({"type": "finish", "status": f"Error: {e}"})
# processing_engine.py
import json
import shutil
import time
from pathlib import Path
from datetime import datetime

import openpyxl
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter

from config import (
    PDF_TXT_DIR,
    CACHE_DIR,
    OUTPUT_DIR,
    STATUS_COLUMN_NAME,
    DESCRIPTION_COLUMN_NAME,
    META_COLUMN_NAME,
    AUTHOR_COLUMN_NAME,
    # --- ADDED: Import BRAND_COLORS to fix the NameError crash. ---
    BRAND_COLORS,
)
from data_harvesters import harvest_all_data
from file_utils import is_file_locked
from ocr_utils import extract_text_from_pdf, _is_ocr_needed
from custom_exceptions import PDFExtractionError


def clear_review_folder():
    if PDF_TXT_DIR.exists():
        for f in PDF_TXT_DIR.glob("*.txt"):
            try:
                f.unlink()
            except OSError as e:
                print(f"Error deleting review file {f}: {e}")

def get_cache_path(pdf_path):
    try:
        return CACHE_DIR / f"{pdf_path.stem}_{pdf_path.stat().st_size}.json"
    except FileNotFoundError:
        return CACHE_DIR / f"{pdf_path.stem}_unknown.json"

def process_single_pdf(pdf_path, progress_queue, ignore_cache=False):
    pdf_path = Path(pdf_path)
    filename = pdf_path.name
    cache_path = get_cache_path(pdf_path)

    progress_queue.put({"type": "log", "tag": "info", "msg": f"Processing: {filename}"})
    
    if not ignore_cache and cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            if "status" not in cached_data:
                raise KeyError
            
            progress_queue.put({"type": "log", "tag": "info", "msg": f"Loaded from cache: {filename}"})
            if cached_data.get("status") == "Needs Review":
                progress_queue.put({"type": "review_item", "data": cached_data})
            elif cached_data.get("status") == "OCR Fail":
                progress_queue.put({"type": "review_item", "data": cached_data})

            progress_queue.put({"type": "file_complete", "status": cached_data.get("status")})
            if cached_data.get("ocr_used"):
                progress_queue.put({"type": "increment_counter", "counter": "ocr"})
            return cached_data
        except (json.JSONDecodeError, KeyError):
             progress_queue.put({"type": "log", "tag": "warning", "msg": f"Corrupt cache for {filename}. Reprocessing..."})

    progress_queue.put({"type": "status", "msg": filename, "led": "Queued"})
    
    absolute_pdf_path = str(pdf_path.resolve())
    ocr_required = _is_ocr_needed(absolute_pdf_path)
    extracted_text = ""
    
    try:
        if ocr_required:
            progress_queue.put({"type": "status", "msg": filename, "led": "OCR"})
            progress_queue.put({"type": "increment_counter", "counter": "ocr"})
        
        extracted_text = extract_text_from_pdf(absolute_pdf_path)

        if ocr_required and not extracted_text.strip():
            progress_queue.put({"type": "ocr_failed"})
            # Mark for review if OCR produced no output
            status = "Needs Review"
            reason = "No text extracted via OCR"
            data = {"models": "Not Found", "author": ""}
        else:
            progress_queue.put({"type": "status", "msg": filename, "led": "AI"})
            data = harvest_all_data(extracted_text, filename)

            if data["models"] == "Not Found":
                status = "Needs Review"
                reason = "Model pattern not found"
            else:
                status = "Pass"
                reason = ""
            
        result = {
            "filename": filename, 
            **data, 
            "status": status, 
            "ocr_used": ocr_required,
            "reason": reason,
            "txt_path": "",
            "pdf_path": str(pdf_path)
        }

    except PDFExtractionError as e:
        progress_queue.put({"type": "log", "tag": "error", "msg": f"Text extraction failed for {filename}: {e}"})
        status = "OCR Fail"
        reason = str(e)
        result = {
            "filename": filename,
            "models": "Error: Text Extraction Failed",
            "author": "",
            "status": status,
            "ocr_used": ocr_required,
            "reason": reason,
            "txt_path": "",
            "pdf_path": str(pdf_path)
        }

    if status in ["Needs Review", "OCR Fail"]:
        review_txt_path = PDF_TXT_DIR / f"{pdf_path.stem}.txt"
        text_to_save = extracted_text if extracted_text else f"File: {filename}\nStatus: {status}\nReason: {reason}"
        with open(review_txt_path, 'w', encoding='utf-8') as f:
            f.write(text_to_save)
        result["txt_path"] = str(review_txt_path)
        progress_queue.put({"type": "review_item", "data": result})

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(result, f)
        
    progress_queue.put({"type": "file_complete", "status": result["status"]})
    return result

def run_processing_job(job_info, progress_queue, cancel_event, pause_event):
    try:
        is_rerun = job_info.get("is_rerun", False)
        excel_path = Path(job_info["excel_path"])
        input_path = job_info["input_path"]
        progress_queue.put({"type": "log", "tag": "info", "msg": "Processing job started."})
        progress_queue.put({"type": "header_status", "text": "Initializing...", "color": BRAND_COLORS["accent_blue"]})


        if is_rerun:
            clear_review_folder()
            cloned_path = excel_path
        else:
            ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            cloned_path = OUTPUT_DIR / f"cloned_{excel_path.stem}_{ts}{excel_path.suffix}"
            if is_file_locked(excel_path):
                progress_queue.put({"type": "log", "tag": "error", "msg": "Input Excel is locked. Cannot create a copy."})
                progress_queue.put({"type": "finish", "status": "Error"})
                return
            shutil.copy(excel_path, cloned_path)
        
        files = [Path(f) for f in input_path] if isinstance(input_path, list) else list(Path(input_path).glob('*.pdf'))
        results = {}
        total_files = len(files)

        for i, path in enumerate(files):
            if cancel_event.is_set():
                break
            if pause_event and pause_event.is_set():
                progress_queue.put({"type": "status", "msg": "Paused", "led": "Paused"})
                progress_queue.put({"type": "header_status", "text": "Paused", "color": BRAND_COLORS["warning_orange"]})
                while pause_event.is_set():
                    time.sleep(0.5)
            
            progress_queue.put({"type": "header_status", "text": f"Processing {i+1}/{total_files}: {path.name}", "color": BRAND_COLORS["accent_blue"]})
            progress_queue.put({"type": "progress", "current": i + 1, "total": total_files})
            
            res = process_single_pdf(path, progress_queue, ignore_cache=is_rerun)
            if res:
                results[res["filename"]] = res

        if cancel_event.is_set():
            progress_queue.put({"type": "finish", "status": "Cancelled"})
            return

        progress_queue.put({"type": "status", "msg": "Updating Excel...", "led": "Saving"})
        progress_queue.put({"type": "header_status", "text": "Saving to Excel...", "color": BRAND_COLORS["success_green"]})

        try:
            workbook = openpyxl.load_workbook(cloned_path)
        except openpyxl.utils.exceptions.InvalidFileException as exc:
            progress_queue.put({"type": "log", "tag": "error", "msg": f"Invalid Excel file: {exc}"})
            progress_queue.put({"type": "finish", "status": "Error"})
            return
            
        sheet = workbook.active
        headers = [c.value for c in sheet[1]]
        if STATUS_COLUMN_NAME not in headers:
            sheet.cell(row=1, column=len(headers) + 1).value = STATUS_COLUMN_NAME
            headers.append(STATUS_COLUMN_NAME)
        cols = {h: headers.index(h) + 1 for h in [DESCRIPTION_COLUMN_NAME, META_COLUMN_NAME, AUTHOR_COLUMN_NAME, STATUS_COLUMN_NAME]}
       
        for row in sheet.iter_rows(min_row=2):
            desc_cell = row[cols[DESCRIPTION_COLUMN_NAME]-1]
            if not desc_cell.value:
                continue
            desc = str(desc_cell.value)
            
            for filename, data in results.items():
                if Path(filename).stem in desc:
                    row[cols[META_COLUMN_NAME]-1].value = data["models"]
                    row[cols[AUTHOR_COLUMN_NAME]-1].value = data["author"]
                    row[cols[STATUS_COLUMN_NAME]-1].value = f"{data['status']}{' (OCR)' if data['ocr_used'] else ''}"
                    break
        
        progress_queue.put({"type": "status", "msg": "Applying formatting...", "led": "Saving"})
        fills = {
            "Pass": PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"),
            "Fail": PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"),
            "Needs Review": PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid"),
            "OCR Fail": PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"),
            "OCR": PatternFill(start_color="0A9BCD", end_color="0A9BCD", fill_type="solid")
        }
        
        for row in sheet.iter_rows(min_row=2):
            status_cell = row[cols[STATUS_COLUMN_NAME]-1]
            if not status_cell.value:
                continue
            status_val = str(status_cell.value)
            
            fill_key = status_val.replace(" (OCR)", "").strip()
            fill = fills.get(fill_key)
            if fill:
                for cell in row:
                    cell.fill = fill
            if "(OCR)" in status_val:
                row[cols[STATUS_COLUMN_NAME]-1].fill = fills["OCR"]
        
        for i, col in enumerate(sheet.columns, 1):
            max_len = max((len(str(c.value)) for c in col if c.value), default=0)
            sheet.column_dimensions[get_column_letter(i)].width = (max_len + 2) if max_len < 60 else 60

        if is_file_locked(cloned_path):
            error_msg = f"Output file '{cloned_path.name}' is locked. Please close it and try again."
            progress_queue.put({"type": "log", "tag": "error", "msg": error_msg})
            progress_queue.put({"type": "locked_file", "path": str(cloned_path)})
            progress_queue.put({"type": "finish", "status": "Error - File Locked"})
            return

        workbook.save(cloned_path)
        progress_queue.put({"type": "result_path", "path": str(cloned_path)})
        progress_queue.put({"type": "finish", "status": "Complete"})

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        progress_queue.put({"type": "log", "tag": "error", "msg": f"Critical error in processing job: {e}\n{error_details}"})
        progress_queue.put({"type": "finish", "status": f"Error: {e}"})

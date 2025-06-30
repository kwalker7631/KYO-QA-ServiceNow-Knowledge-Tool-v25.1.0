# processing_engine.py
import shutil, time, json, openpyxl, re
import threading
from queue import Queue
from pathlib import Path
from datetime import datetime
from openpyxl.styles import PatternFill, Alignment
from openpyxl.utils import get_column_letter

from config import *
from custom_exceptions import FileLockError
from data_harvesters import harvest_all_data
from file_utils import is_file_locked
from ocr_utils import extract_text_from_pdf, _is_ocr_needed

def clear_review_folder():
    if NEEDS_REVIEW_DIR.exists():
        for f in NEEDS_REVIEW_DIR.glob("*.txt"):
            try:
                f.unlink()
            except OSError as e:
                print(f"Error deleting review file {f}: {e}")

def get_cache_path(pdf_path):
    try: return CACHE_DIR / f"{pdf_path.stem}_{pdf_path.stat().st_size}.json"
    except FileNotFoundError: return CACHE_DIR / f"{pdf_path.stem}_unknown.json"

def process_single_pdf(pdf_path, progress_queue, ignore_cache=False):
    filename, cache_path = pdf_path.name, get_cache_path(pdf_path)
    if not ignore_cache and cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f: cached_data = json.load(f)
            if "status" not in cached_data: raise KeyError
            
            progress_queue.put({"type": "log", "tag": "info", "msg": f"Loaded from cache: {filename}"})
            if cached_data.get("status") == "Needs Review":
                progress_queue.put({"type": "review_item", "data": cached_data.get("review_info")})
            progress_queue.put({"type": "file_complete", "status": cached_data.get("status")})
            if cached_data.get("ocr_used"): progress_queue.put({"type": "increment_counter", "counter": "ocr"})
            return cached_data
        except (json.JSONDecodeError, KeyError):
             progress_queue.put({"type": "log", "tag": "warning", "msg": f"Corrupt cache for {filename}. Reprocessing..."})

    progress_queue.put({"type": "status", "msg": filename, "led": "Queued"})
    ocr_required = _is_ocr_needed(pdf_path)
    if ocr_required:
        progress_queue.put({"type": "status", "msg": filename, "led": "OCR"})
        progress_queue.put({"type": "increment_counter", "counter": "ocr"})
    
    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text.strip():
        result = {"filename": filename, "models": "Error: Text Extraction Failed", "author": "", "status": "Fail", "ocr_used": ocr_required, "review_info": None}
    else:
        progress_queue.put({"type": "status", "msg": filename, "led": "AI"})
        data = harvest_all_data(extracted_text, filename)
        if data["models"] == "Not Found":
            status = "Needs Review"
            NEEDS_REVIEW_DIR.mkdir(parents=True, exist_ok=True)
            review_txt_path = NEEDS_REVIEW_DIR / f"{filename}.txt"
            with open(review_txt_path, 'w', encoding='utf-8') as f:
                f.write(f"--- Filename: {filename} ---\n\n{extracted_text}")
            review_info = {
                "filename": filename,
                "reason": "No models",
                "txt_path": str(review_txt_path),
                "pdf_path": str(pdf_path),
            }
            progress_queue.put({"type": "review_item", "data": review_info})
        else:
            status = "Pass"; review_info = None
        result = {"filename": filename, **data, "status": status, "ocr_used": ocr_required, "review_info": review_info}

    with open(cache_path, 'w', encoding='utf-8') as f: json.dump(result, f)
    progress_queue.put({"type": "file_complete", "status": result["status"]})
    return result

def run_processing_job(job_info, progress_queue, cancel_event, pause_event):
    try:
        is_rerun = job_info.get("is_rerun", False)
        excel_path = Path(job_info["excel_path"])
        input_path = job_info["input_path"]
        progress_queue.put({"type": "log", "tag": "info", "msg": "Processing job started."})

        if is_rerun:
            clear_review_folder()
            cloned_path = excel_path
        else:
            ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            cloned_path = OUTPUT_DIR / f"cloned_{excel_path.stem}_{ts}{excel_path.suffix}"
            if is_file_locked(excel_path): raise FileLockError("Input Excel is locked.")
            shutil.copy(excel_path, cloned_path)
        
        files = [Path(f) for f in input_path] if isinstance(input_path, list) else list(Path(input_path).glob('*.pdf'))
        results = {}
        for i, path in enumerate(files):
            if cancel_event.is_set(): break
            if pause_event.is_set():
                progress_queue.put({"type": "status", "msg": "Paused", "led": "Paused"})
                while pause_event.is_set(): time.sleep(0.5)
            progress_queue.put({"type": "progress", "current": i + 1, "total": len(files)})
            res = process_single_pdf(path, progress_queue, ignore_cache=is_rerun)
            if res is None: res = process_single_pdf(path, progress_queue, ignore_cache=True)
            results[res["filename"]] = res

        if cancel_event.is_set():
            progress_queue.put({"type": "finish", "status": "Cancelled"}); return

        progress_queue.put({"type": "status", "msg": "Updating Excel...", "led": "Saving"})
        workbook = openpyxl.load_workbook(cloned_path)
        sheet = workbook.active
        headers = [c.value for c in sheet[1]]
        
        if STATUS_COLUMN_NAME not in headers:
            sheet.cell(row=1, column=len(headers) + 1).value = STATUS_COLUMN_NAME
            headers.append(STATUS_COLUMN_NAME)
            
        try:
            col_indices = {h: headers.index(h) + 1 for h in [DESCRIPTION_COLUMN_NAME, META_COLUMN_NAME, AUTHOR_COLUMN_NAME, STATUS_COLUMN_NAME]}
        except ValueError as e: raise ValueError(f"Column not found in Excel: {e}")

        updates, appends = 0, 0
        pdfs_found = set()
        for row_idx in range(2, sheet.max_row + 1):
            desc = str(sheet.cell(row=row_idx, column=col_indices[DESCRIPTION_COLUMN_NAME]).value)
            for filename, data in results.items():
                if Path(filename).stem in desc:
                    meta_cell = sheet.cell(row=row_idx, column=col_indices[META_COLUMN_NAME])
                    if meta_cell.value is None or str(meta_cell.value).strip() in ["", "Review Needed"]:
                        meta_cell.value = data["models"]; updates += 1
                    sheet.cell(row=row_idx, column=col_indices[AUTHOR_COLUMN_NAME]).value = data.get("author", "")
                    sheet.cell(row=row_idx, column=col_indices[STATUS_COLUMN_NAME]).value = f"{data['status']}{' (OCR)' if data['ocr_used'] else ''}"
                    pdfs_found.add(filename); break
        
        pdfs_to_add = [data for filename, data in results.items() if filename not in pdfs_found]
        if pdfs_to_add:
            for data in pdfs_to_add:
                new_row = [""] * len(headers)
                new_row[col_indices[DESCRIPTION_COLUMN_NAME] - 1] = data.get("filename")
                new_row[col_indices[META_COLUMN_NAME] - 1] = data["models"]
                new_row[col_indices[AUTHOR_COLUMN_NAME] - 1] = data.get("author", "")
                new_row[col_indices[STATUS_COLUMN_NAME] - 1] = f"{data['status']}{' (OCR)' if data['ocr_used'] else ''}"
                sheet.append(new_row); appends += 1
        progress_queue.put({"type": "log", "tag": "info", "msg": f"{updates} rows updated, {appends} new rows appended."})
        
        progress_queue.put({"type": "status", "msg": "Applying formatting...", "led": "Saving"})
        fills = {"Pass": PatternFill("solid", fgColor="C6EFCE"), "Fail": PatternFill("solid", fgColor="FFC7CE"), "Needs Review": PatternFill("solid", fgColor=BRAND_COLORS["warning_yellow"]), "OCR": PatternFill("solid", fgColor=BRAND_COLORS["accent_blue"])}
        wrap_alignment = Alignment(wrap_text=True, vertical='top')
        
        for row in sheet.iter_rows(min_row=2, max_row=sheet.max_row):
            status_val = str(row[col_indices[STATUS_COLUMN_NAME]-1].value)
            fill_to_apply = next((fills[key] for key in fills if key in status_val), None)
            for cell in row:
                if fill_to_apply: cell.fill = fill_to_apply
                cell.alignment = wrap_alignment
            if "(OCR)" in status_val: row[col_indices[STATUS_COLUMN_NAME]-1].fill = fills["OCR"]
        
        for i, col_cells in enumerate(sheet.columns, 1):
            max_len = max((len(str(c.value)) for c in col_cells if c.value), default=0)
            sheet.column_dimensions[get_column_letter(i)].width = (max_len + 2) if max_len < 60 else 60

        progress_queue.put({"type": "status", "msg": "Saving final XLSX file...", "led": "Saving"})
        workbook.save(cloned_path)
        progress_queue.put({"type": "log", "tag": "success", "msg": f"Successfully saved: {cloned_path.name}"})
        progress_queue.put({"type": "result_path", "path": str(cloned_path)})
        progress_queue.put({"type": "finish", "status": "Complete"})

    except Exception as e:
        error_message = f"A critical error occurred: {e}"
        progress_queue.put({"type": "log", "tag": "error", "msg": error_message})
        progress_queue.put({"type": "finish", "status": f"Error: {e}"})


def process_folder(folder_path, excel_path, *_, **__):
    """Legacy CLI wrapper to process all PDFs in a folder."""
    progress_queue = Queue()
    cancel_event = threading.Event()
    pause_event = threading.Event()
    job = {"excel_path": excel_path, "input_path": folder_path}
    run_processing_job(job, progress_queue, cancel_event, pause_event)


def process_zip_archive(zip_path, excel_path, *args, **kwargs):
    """Legacy CLI wrapper to process a ZIP of PDFs."""
    import tempfile, zipfile
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmpdir)
        process_folder(tmpdir, excel_path, *args, **kwargs)

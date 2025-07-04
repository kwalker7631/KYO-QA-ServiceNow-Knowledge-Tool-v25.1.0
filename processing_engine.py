import os
import pandas as pd
import logging
import shutil
from pathlib import Path
import time
import re

# Local module imports
from ocr_utils import get_text_from_pdf
from data_harvesters import harvest_all_data
from file_utils import (
    create_temp_working_dir,
    setup_output_folders,
    cleanup_directory
)
from excel_generator import ExcelGenerator
from custom_exceptions import PDFExtractionError, ExcelGenerationError

logger = logging.getLogger("app.engine")

def run_processing_job(job_details: dict, response_queue, cancel_event, pause_event):
    """
    The main function to orchestrate the entire file processing workflow.
    This version is based on the stable v25.1.1 logic with v26 error handling.
    """
    input_path = job_details.get("input_path")
    excel_path = job_details.get("excel_path")
    output_dir = Path(job_details.get("output_dir"))
    is_rerun = job_details.get("is_rerun", False)
    temp_dir = None
    
    try:
        logger.info("--- Starting New Processing Job ---")
        response_queue.put({"type": "log", "msg": "Initializing..."})
        
        temp_dir = create_temp_working_dir()
        if not temp_dir:
            raise Exception("Failed to create temporary directory.")
        
        output_folders = setup_output_folders(output_dir)
        locked_files_dir = output_folders.get("locked_files")
        review_files_dir = output_folders.get("needs_review")

        # Determine the source directory
        if is_rerun:
            source_dir = Path(review_files_dir)
            source_files = [f for f in source_dir.iterdir() if f.is_file() and f.suffix.lower() == '.txt']
        elif isinstance(input_path, list):
             source_files = [Path(p) for p in input_path if Path(p).suffix.lower() in ['.pdf', '.txt']]
        else: # It's a folder path
            source_dir = Path(input_path)
            source_files = [f for f in source_dir.rglob('*') if f.is_file() and f.suffix.lower() in ['.pdf', '.txt']]

        response_queue.put({"type": "log", "msg": f"Found {len(source_files)} files to process."})
        
        if not source_files:
            response_queue.put({"type": "log", "msg": "No valid files found.", "tag": "warning"})
            return

        all_harvested_data = []
        total_files = len(source_files)
        
        for i, src_path in enumerate(source_files):
            if cancel_event.is_set():
                response_queue.put({"type": "log", "msg": "Processing cancelled."})
                break
            
            while pause_event.is_set():
                time.sleep(0.5)

            filename = src_path.name
            response_queue.put({"type": "status", "msg": f"Processing: {filename}"})
            response_queue.put({"type": "progress", "value": (i / total_files) * 100})
            
            try:
                text_content = ""
                if src_path.suffix.lower() == '.pdf':
                    # Copy to temp location to avoid locking the original
                    temp_pdf_path = temp_dir / filename
                    shutil.copy(src_path, temp_pdf_path)
                    text_content = get_text_from_pdf(temp_pdf_path)
                else: # .txt file
                    text_content = src_path.read_text(encoding='utf-8', errors='ignore')

                qa_number = src_path.stem
                harvested_data = harvest_all_data(text_content, qa_number)
                
                if not harvested_data.get("models"):
                    logger.warning(f"No models found for {filename}. Flagging for review.")
                    if review_files_dir:
                        review_txt_path = review_files_dir / f"{qa_number}.txt"
                        review_txt_path.write_text(text_content, encoding='utf-8')
                    harvested_data["status"] = "Needs Review"
                else:
                    harvested_data["status"] = "Pass"

                all_harvested_data.append(harvested_data)

            except (OSError, shutil.Error) as e:
                logger.error(f"Could not access or copy '{filename}': {e}. Skipping.")
                response_queue.put({"type": "log", "msg": f"SKIPPED (locked): {filename}", "tag": "warning"})
                if locked_files_dir:
                    try:
                        shutil.copy(src_path, locked_files_dir / filename)
                    except Exception as final_e:
                        logger.error(f"Failed to move locked file {filename}: {final_e}")
            except PDFExtractionError as e:
                logger.error(f"Failed to extract text from {filename}: {e}")
                response_queue.put({"type": "log", "msg": f"ERROR processing {filename}: {e}", "tag": "error"})
            except Exception as e:
                logger.error(f"An unexpected error occurred while processing {filename}: {e}", exc_info=True)

        if not cancel_event.is_set() and all_harvested_data:
            response_queue.put({"type": "log", "msg": "Generating Excel report..."})
            try:
                report_path = output_dir / f"cloned_{Path(excel_path).name}"
                generator = ExcelGenerator(report_path)
                generator.create_report(all_harvested_data)
                response_queue.put({"type": "result_path", "path": str(report_path)})
            except Exception as e:
                raise ExcelGenerationError(f"Failed to generate Excel report: {e}")

    except Exception as e:
        logger.critical(f"A critical error occurred in the processing job: {e}", exc_info=True)
        response_queue.put({"type": "log", "msg": f"CRITICAL ERROR: {e}", "tag": "error"})
    finally:
        if temp_dir:
            cleanup_directory(temp_dir)
        status = "Cancelled" if cancel_event.is_set() else "Complete"
        response_queue.put({"type": "finish", "status": status})
        logger.info(f"--- Processing Job Finished with status: {status} ---")

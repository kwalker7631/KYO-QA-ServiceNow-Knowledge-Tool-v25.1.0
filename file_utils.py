# file_utils.py - Enhanced file and directory management
import shutil
from pathlib import Path
import os
import sys

from logging_utils import setup_logger, log_info, log_error
from config import PDF_TXT_DIR

logger = setup_logger("file_management")

def ensure_review_folders():
    """
    Ensure NEED_REVIEW and OCR_FAILED folders exist.
    Rename existing PDF_TXT to NEED_REVIEW if needed.
    """
    try:
        # Ensure base directory exists
        base_dir = Path(PDF_TXT_DIR)
        base_dir.mkdir(parents=True, exist_ok=True)

        # Check and rename existing PDF_TXT if it exists
        if base_dir.exists() and base_dir.name == "PDF_TXT":
            new_name = base_dir.with_name("NEED_REVIEW")
            base_dir.rename(new_name)
            log_info(logger, f"Renamed {base_dir} to {new_name}")

        # Create NEED_REVIEW and OCR_FAILED folders
        need_review_dir = base_dir / "NEED_REVIEW"
        ocr_failed_dir = base_dir / "OCR_FAILED"

        need_review_dir.mkdir(parents=True, exist_ok=True)
        ocr_failed_dir.mkdir(parents=True, exist_ok=True)

        return need_review_dir, ocr_failed_dir
    except Exception as e:
        log_error(logger, f"Error setting up review folders: {e}")
        return None, None

def move_to_review_folder(file_path, reason='', folder_type='NEED_REVIEW'):
    """
    Move a file to the appropriate review folder with logging.
    
    Args:
        file_path: Path to the file to move
        reason: Reason for moving the file
        folder_type: 'NEED_REVIEW' or 'OCR_FAILED'
    
    Returns:
        Path to the new location of the file
    """
    try:
        file_path = Path(file_path)
        need_review_dir, ocr_failed_dir = ensure_review_folders()
        
        if folder_type == 'NEED_REVIEW':
            dest_dir = need_review_dir
        elif folder_type == 'OCR_FAILED':
            dest_dir = ocr_failed_dir
        else:
            log_error(logger, f"Invalid folder type: {folder_type}")
            return None
        
        dest_path = dest_dir / file_path.name
        
        # Ensure unique filename if one already exists
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
            counter += 1
        
        # Move the file
        shutil.move(str(file_path), str(dest_path))
        
        log_info(logger, f"Moved {file_path.name} to {dest_path} - Reason: {reason}")
        return dest_path
    except Exception as e:
        log_error(logger, f"Error moving {file_path} to review folder: {e}")
        return None

def open_review_folder():
    """
    Open the NEED_REVIEW folder in the system's file browser.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        need_review_dir, _ = ensure_review_folders()
        
        if not need_review_dir:
            log_error(logger, "Could not locate NEED_REVIEW folder")
            return False
        
        # Platform-specific file browser opening
        if sys.platform == 'win32':
            os.startfile(str(need_review_dir))
        elif sys.platform == 'darwin':  # macOS
            os.system(f'open "{need_review_dir}"')
        else:  # linux variants
            os.system(f'xdg-open "{need_review_dir}"')
        
        log_info(logger, f"Opened NEED_REVIEW folder: {need_review_dir}")
        return True
    except Exception as e:
        log_error(logger, f"Error opening review folder: {e}")
        return False

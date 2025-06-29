# KYO QA ServiceNow File Utilities
from version import VERSION

import os
import shutil
import time
from pathlib import Path
from logging_utils import setup_logger, log_info, log_error, log_warning
from datetime import datetime

logger = setup_logger("file_utils")

# Ensure all needed subfolders exist
REQUIRED_FOLDERS = [
    "logs",
    "output",
    "PDF_TXT",
    "temp"
    # add more as needed
]

def ensure_folders(base_folder=None):
    base = Path(base_folder) if base_folder else Path(__file__).parent
    for folder in REQUIRED_FOLDERS:
        fpath = base / folder
        try:
            fpath.mkdir(parents=True, exist_ok=True)
            log_info(logger, f"Ensured folder exists: {fpath}")
        except Exception as e:
            log_error(logger, f"Failed to create folder {fpath}: {e}")
    return base

def get_temp_dir():
    """Get the path to the temp directory."""
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir

def is_pdf(filename):
    """Check if a file is a PDF based on extension."""
    return str(filename).lower().endswith(".pdf")

def is_zip(filename):
    """Check if a file is a ZIP based on extension."""
    return str(filename).lower().endswith(".zip")

def is_excel(filename):
    """Check if a file is an Excel file (.xlsx or .xlsm)."""
    return str(filename).lower().endswith((".xlsx", ".xlsm"))

def save_txt(text, output_path):
    """Save text to a file with proper encoding."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        log_info(logger, f"Saved TXT: {output_path}")
        return True
    except Exception as e:
        log_error(logger, f"Failed to save TXT: {output_path} - {e}")
        return False

def cleanup_temp_files(directory=None):
    """Clean up temporary files."""
    if directory is None:
        directory = get_temp_dir()
    
    try:
        # Remove files older than 1 day
        now = datetime.now().timestamp()
        count = 0
        
        for item in Path(directory).glob("**/*"):
            if item.is_file():
                file_age = now - item.stat().st_mtime
                if file_age > 86400:  # 24 hours in seconds
                    try:
                        item.unlink()
                        count += 1
                    except Exception as e:
                        log_warning(logger, f"Could not delete {item}: {e}")
        
        # Remove empty directories
        for root, dirs, files in os.walk(directory, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                except Exception as e:
                    log_warning(logger, f"Could not remove directory {dir_path}: {e}")
        
        log_info(logger, f"Cleaned up {count} temporary files")
        return count
    except Exception as e:
        log_error(logger, f"Failed to clean up temporary files: {e}")
        return 0

def copy_file_safely(source_path, dest_path, retries=3, wait_time=1.0):
    """
    Copy a file with retry mechanism for cloud storage issues.
    
    Args:
        source_path: Path to source file
        dest_path: Path to destination file
        retries: Number of retry attempts
        wait_time: Time to wait between retries in seconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    source_path = Path(source_path)
    dest_path = Path(dest_path)
    
    if not source_path.exists():
        log_error(logger, f"Source file does not exist: {source_path}")
        return False
    
    # Ensure parent directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(retries):
        try:
            # For small files, direct copy should work
            if source_path.stat().st_size < 10 * 1024 * 1024:  # Less than 10MB
                shutil.copy2(source_path, dest_path)
                log_info(logger, f"Copied {source_path} to {dest_path}")
                return True
            
            # For larger files, use chunk-by-chunk copy
            with open(source_path, 'rb') as src, open(dest_path, 'wb') as dst:
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
            
            log_info(logger, f"Copied {source_path} to {dest_path} in chunks")
            return True
            
        except Exception as e:
            log_warning(logger, f"Copy attempt {attempt+1}/{retries} failed: {e}")
            time.sleep(wait_time)
    
    log_error(logger, f"Failed to copy {source_path} to {dest_path} after {retries} attempts")
    return False

def open_file(file_path):
    """
    Open a file with the default system application.
    
    Args:
        file_path: Path to the file to open
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            log_error(logger, f"File does not exist: {file_path}")
            return False
        
        import sys
        import subprocess
        
        if sys.platform == 'win32':
            os.startfile(file_path)
            log_info(logger, f"Opened {file_path} with default Windows application")
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', str(file_path)], check=True)
            log_info(logger, f"Opened {file_path} with default macOS application")
        else:  # Linux
            subprocess.run(['xdg-open', str(file_path)], check=True)
            log_info(logger, f"Opened {file_path} with default Linux application")
            
        return True
        
    except Exception as e:
        log_error(logger, f"Failed to open {file_path}: {e}")
        return False
# ... (all other functions remain the same) ...

# --- NEW UTILITY FUNCTION ---
def is_file_locked(filepath: Path) -> bool:
    """
    Checks if a file is locked by another process by trying to open it for appending.
    """
    if not filepath.exists():
        return False # File doesn't exist, so it can't be locked
    
    try:
        # Try to open the file in append mode. If it's locked, this will fail.
        with open(filepath, 'a') as f:
            pass # We don't need to do anything, just successfully open and close it.
    except (IOError, PermissionError):
        # This exception means the file is locked by another process (like Excel).
        log_warning(logger, f"File lock check failed. File is likely open: {filepath}")
        return True
    
    return False
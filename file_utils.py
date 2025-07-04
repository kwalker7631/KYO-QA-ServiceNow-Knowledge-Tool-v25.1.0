# file_utils.py
# Version: 26.0.0 (Repaired)
# Last modified: 2025-07-03
# Provides utility functions for file and folder management.

import os
import sys
import shutil
from pathlib import Path
import subprocess
import platform

# --- Application Modules ---
from config import LOGS_DIR, OUTPUT_DIR, PDF_TXT_DIR, CACHE_DIR
import logging_utils

logger = logging_utils.setup_logger("file_utils")

def ensure_folders():
    """Create all necessary application folders on startup if they don't exist."""
    logger.info("Ensuring all required application directories exist.")
    for folder in [LOGS_DIR, OUTPUT_DIR, PDF_TXT_DIR, CACHE_DIR]:
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create directory {folder}: {e}")

def is_file_locked(filepath: Path) -> bool:
    """
    REPAIRED: Checks if a file is locked by another process. This is critical
    for preventing errors when writing to the Excel report.
    """
    try:
        # Try to open the file in append mode. If it's locked by another
        # program (like Excel), this will raise an IOError.
        with open(filepath, "a"):
            pass
        return False
    except IOError:
        logger.warning(f"File is locked: {filepath.name}")
        return True
    except Exception as e:
        logger.error(f"Unexpected error checking file lock for {filepath.name}: {e}")
        return True # Assume locked on unexpected error to be safe

def cleanup_temp_files():
    """Removes temporary files from cache and review folders upon closing."""
    logger.info("Cleaning up temporary files from cache and review folders.")
    for directory in [CACHE_DIR, PDF_TXT_DIR]:
        if directory.exists():
            for item in directory.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except OSError as e:
                    logger.error(f"Error deleting temporary item {item}: {e}")

def open_file(path: str | Path):
    """Opens a file or folder with the default system application."""
    path_str = str(path)
    logger.info(f"Attempting to open {path_str} with default application.")
    try:
        if platform.system() == "Windows":
            os.startfile(path_str)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path_str], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", path_str], check=True)
    except Exception as e:
        logger.error(f"Failed to open file or folder '{path_str}': {e}")
        # Optionally, show this error to the user in a messagebox if it were called from the UI thread

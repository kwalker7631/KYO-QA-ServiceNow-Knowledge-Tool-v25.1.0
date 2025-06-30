# file_utils.py
import os
import sys
import shutil
from pathlib import Path

from config import LOGS_DIR, OUTPUT_DIR, PDF_TXT_DIR, CACHE_DIR

def ensure_folders():
    """Create all necessary application folders on startup."""
    for folder in [LOGS_DIR, OUTPUT_DIR, PDF_TXT_DIR, CACHE_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

def is_file_locked(filepath):
    """Check if a file is locked by another process."""
    try:
        # Try to open the file in append mode. If it's locked, this will fail.
        with open(filepath, "a"):
            pass
    except IOError:
        return True
    return False

# --- UPDATED FUNCTION ---
def cleanup_temp_files():
    """Removes temporary files from cache and review folders."""
    print("Cleaning up temporary files...")
    for directory in [CACHE_DIR, PDF_TXT_DIR]:
        if directory.exists():
            for item in directory.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except OSError as e:
                    # Log an error if a file can't be removed
                    print(f"Error deleting {item}: {e}")
    print("Cleanup complete.")
# --- END OF UPDATE ---

def open_file(path: str | Path):
    """Opens a file with the default system application."""
    path = str(path)
    if hasattr(os, 'startfile'): # For Windows
        os.startfile(path)
    else: # For macOS and Linux
        import subprocess
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path])
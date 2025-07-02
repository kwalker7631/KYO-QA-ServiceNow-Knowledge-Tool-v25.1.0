# file_utils.py
import os
import sys
import shutil
from pathlib import Path

from config import LOGS_DIR, OUTPUT_DIR, PDF_TXT_DIR, CACHE_DIR

def ensure_folders():
    """Create all necessary application folders on startup."""
    for folder in [LOGS_DIR, OUTPUT_DIR, CACHE_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
    PDF_TXT_DIR.mkdir(parents=True, exist_ok=True)

def is_file_locked(filepath):
    """Check if a file is locked by another process."""
    filepath = str(filepath)
    if os.name == "nt":
        try:
            import msvcrt
            fh = open(filepath, "a")
            try:
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            finally:
                fh.close()
            return False
        except OSError:
            return True
    else:
        try:
            import fcntl
            with open(filepath, "a") as f:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(f, fcntl.LOCK_UN)
            return False
        except (OSError, IOError):
            return True

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

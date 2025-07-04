import os
import sys
import shutil
import tempfile
import logging
from tkinter import messagebox
from pathlib import Path
import stat # <-- Required for changing file attributes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def try_unlock_file(filepath: Path) -> bool:
    """
    Attempts to remove the read-only attribute from a file.
    Returns True if the operation was attempted, False otherwise.
    """
    try:
        # Get current permissions and add write permission for the owner
        current_permissions = os.stat(filepath).st_mode
        os.chmod(filepath, current_permissions | stat.S_IWRITE)
        logging.info(f"Attempted to remove read-only attribute from {filepath.name}")
        return True
    except (OSError, PermissionError) as e:
        logging.warning(f"Could not change file attributes for {filepath.name}: {e}")
        return False

def get_resource_path(relative_path):
    """
    Get the absolute path to a resource, works for both development and for PyInstaller.
    """
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path.cwd()
    return base_path / relative_path

def find_tesseract_executable():
    """
    Find the tesseract.exe executable in a prioritized order.
    """
    logging.info("Searching for Tesseract executable...")
    
    search_paths = []
    if getattr(sys, 'frozen', False):
        search_paths.append(Path(sys._MEIPASS) / 'Tesseract-OCR' / 'tesseract.exe')
    
    search_paths.extend([
        Path.cwd() / 'Tesseract-OCR' / 'tesseract.exe',
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Tesseract-OCR" / "tesseract.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe"
    ])

    for path in search_paths:
        if path.exists():
            logging.info(f"Found Tesseract at: {path}")
            return str(path)

    error_message = "Tesseract OCR executable not found. Please ensure Tesseract is installed and accessible."
    logging.error(error_message)
    messagebox.showerror("Dependency Error", error_message)
    raise FileNotFoundError(error_message)

def is_file_locked(filepath):
    """
    Checks if a file is locked by attempting to open it in append mode.
    """
    try:
        with open(filepath, 'a+b'):
            pass
        return False
    except (IOError, PermissionError) as e:
        logging.warning(f"File is locked: {filepath}. Reason: {e}")
        return True

def create_temp_working_dir():
    """
    Creates a temporary directory to safely store and process file copies.
    """
    try:
        temp_dir = tempfile.mkdtemp(prefix="kyo_qa_")
        logging.info(f"Created temporary working directory: {temp_dir}")
        return Path(temp_dir)
    except Exception as e:
        logging.error(f"Failed to create temporary directory: {e}")
        messagebox.showerror("Error", f"Could not create a temporary working directory: {e}")
        return None

def cleanup_directory(directory_path):
    """
    Recursively deletes the specified directory and all its contents.
    """
    if not directory_path or not os.path.exists(directory_path):
        logging.warning(f"Cleanup skipped: Directory does not exist or path is invalid: {directory_path}")
        return
        
    try:
        shutil.rmtree(directory_path)
        logging.info(f"Successfully cleaned up directory: {directory_path}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during cleanup of {directory_path}: {e}")
        messagebox.showwarning("Cleanup Failed", f"An error occurred while cleaning up files:\n{e}")

def setup_output_folders(base_dir):
    """
    Creates all necessary output subdirectories and returns their Path objects.
    """
    base_path = Path(base_dir)
    try:
        locked_files_dir = base_path / "locked_files"
        needs_review_dir = base_path / "needs_review"
        
        locked_files_dir.mkdir(parents=True, exist_ok=True)
        needs_review_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "locked_files": locked_files_dir,
            "needs_review": needs_review_dir
        }
    except Exception as e:
        logging.error(f"Could not create output subdirectories in {base_dir}: {e}")
        return {}

# --- Compatibility Functions ---
def open_file(filepath):
    """Opens a file with the default application."""
    try:
        os.startfile(filepath)
    except Exception as e:
        logging.error(f"Failed to open file {filepath}: {e}")
        messagebox.showerror("Error", f"Could not open the file:\n{filepath}")

def ensure_folders(base_dir):
    """Alias for setup_output_folders for backward compatibility."""
    logging.warning("Using deprecated function 'ensure_folders'. Please switch to 'setup_output_folders'.")
    return setup_output_folders(base_dir)

def cleanup_temp_files(directory_path):
    """Alias for cleanup_directory for backward compatibility."""
    logging.warning("Using deprecated function 'cleanup_temp_files'. Please switch to 'cleanup_directory'.")
    cleanup_directory(directory_path)

# file_utils.py
import os
import shutil
import tempfile
from pathlib import Path
import subprocess
import platform

# Create a temporary directory for storing intermediate files
def get_temp_dir():
    """Returns a Path object to a temporary directory that will be used for this session."""
    temp_dir = Path(tempfile.gettempdir()) / "kyo_qa_tool_temp"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir

def cleanup_temp_files():
    """Clean up any temporary files created during processing."""
    temp_dir = get_temp_dir()
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            # Ignore errors when cleaning up temp files
            pass

def ensure_folders():
    """Ensure all required folders exist."""
    # Import here to avoid circular imports
    from config import OUTPUT_DIR, PDF_TXT_DIR
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    PDF_TXT_DIR.mkdir(exist_ok=True)
    
    temp_dir = get_temp_dir()
    temp_dir.mkdir(exist_ok=True)

def is_file_locked(filepath):
    """
    Check if a file is locked by another process.
    
    Args:
        filepath: Path to the file to check
        
    Returns:
        bool: True if the file is locked, False otherwise
    """
    if not Path(filepath).exists():
        return False
        
    try:
        # Try to open the file in read and write mode
        with open(filepath, 'r+b') as f:
            # Try to lock the file exclusively to see if it's locked by another process
            # This is a Windows-specific solution, but it will work for our needs
            try:
                # Using the msvcrt module for Windows only
                if platform.system() == 'Windows':
                    import msvcrt
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBRLCK, 1)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    # On Unix systems, try to use fcntl
                    try:
                        import fcntl
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except ImportError:
                        # If fcntl is not available, just try to write to the file
                        current_position = f.tell()
                        f.seek(0, os.SEEK_END)
                        f.seek(current_position)
                return False  # If we got this far, the file is not locked
            except (IOError, PermissionError):
                return True  # File is locked
    except (IOError, PermissionError):
        return True  # Cannot open the file, assume it's locked

def open_file(file_path):
    """
    Open a file with the default application for its type.
    
    Args:
        file_path: Path to the file to open
    """
    file_path = str(file_path)
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path], check=True)
        else:  # Linux and other Unix-like
            subprocess.run(['xdg-open', file_path], check=True)
    except Exception as e:
        print(f"Failed to open file: {e}")

def get_file_extension(filename):
    """Returns the file extension in lowercase, e.g., '.pdf'."""
    if not filename or not isinstance(filename, str):
        return ""
    return os.path.splitext(filename)[1].lower()
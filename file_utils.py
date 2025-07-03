# file_utils.py
# Version: 26.0.0
# Last modified: 2025-07-03
# Essential file and directory management utilities

import shutil
import os
import sys
from pathlib import Path

# Import config without logging to avoid circular imports
from config import (
    OUTPUT_DIR,
    LOGS_DIR,
    NEED_REVIEW_DIR,
    OCR_FAILED_DIR,
    PDF_TXT_DIR,
    CACHE_DIR,
)


def is_file_locked(file_path):
    """
    Check if a file is locked by another process.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if file is locked, False otherwise
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False
    
    try:
        if sys.platform == "win32":
            # On Windows, try to open the file for writing
            try:
                with open(file_path, 'r+b') as f:
                    pass
                return False
            except (OSError, PermissionError):
                return True
        else:
            # On Unix-like systems, try fcntl if available
            try:
                import fcntl
                with open(file_path, 'r+b') as f:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(f, fcntl.LOCK_UN)
                return False
            except ImportError:
                # fcntl not available, use simple file access test
                try:
                    with open(file_path, 'r+b') as f:
                        pass
                    return False
                except (OSError, IOError):
                    return True
            except (OSError, IOError):
                return True
    except Exception:
        return False


def ensure_folders():
    """
    Ensure all required directories exist.
    Create missing directories and migrate old folder structures.
    """
    try:
        # List of directories that need to exist
        required_dirs = [
            OUTPUT_DIR,
            LOGS_DIR,
            CACHE_DIR,
            NEED_REVIEW_DIR,
            OCR_FAILED_DIR,
        ]
        
        # Create all required directories
        for directory in required_dirs:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Create needs_review subdirectory
        needs_review_subdir = NEED_REVIEW_DIR / "needs_review"
        needs_review_subdir.mkdir(parents=True, exist_ok=True)
        
        # Handle legacy PDF_TXT directory migration
        old_pdf_txt = Path("PDF_TXT")
        if old_pdf_txt.exists() and old_pdf_txt != NEED_REVIEW_DIR:
            try:
                # Move contents to new location
                for item in old_pdf_txt.iterdir():
                    dest = NEED_REVIEW_DIR / item.name
                    if item.is_file():
                        shutil.move(str(item), str(dest))
                    elif item.is_dir():
                        shutil.move(str(item), str(dest))
                
                # Remove old directory if empty
                if not any(old_pdf_txt.iterdir()):
                    old_pdf_txt.rmdir()
            except Exception:
                pass  # Silently ignore migration errors
        
    except Exception:
        pass  # Silently ignore folder creation errors for now


def move_to_folder(file_path, dest_folder, reason=""):
    """
    Move a file to a destination folder.
    
    Args:
        file_path: Path to the file to move
        dest_folder: Destination folder path
        reason: Reason for moving the file
        
    Returns:
        Path: New location of the file, or None if move failed
    """
    try:
        file_path = Path(file_path)
        dest_folder = Path(dest_folder)
        
        # Ensure destination folder exists
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        # Generate unique destination filename
        dest_path = dest_folder / file_path.name
        counter = 1
        while dest_path.exists():
            dest_path = dest_folder / f"{file_path.stem}_{counter}{file_path.suffix}"
            counter += 1
        
        # Move the file
        shutil.move(str(file_path), str(dest_path))
        return dest_path
        
    except Exception:
        return None


def open_file(file_path):
    """
    Open a file or directory with the default system application.
    
    Args:
        file_path: Path to file or directory to open
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        if sys.platform == "win32":
            os.startfile(str(file_path))
        elif sys.platform == "darwin":  # macOS
            import subprocess
            subprocess.run(["open", str(file_path)])
        else:  # Linux and other Unix-like systems
            import subprocess
            subprocess.run(["xdg-open", str(file_path)])
        
        return True
        
    except Exception:
        return False


def get_safe_filename(filename, max_length=255):
    """
    Convert a string to a safe filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename string
        max_length: Maximum length for the filename
        
    Returns:
        str: Safe filename string
    """
    import re
    
    # Remove invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', str(filename))
    
    # Remove control characters
    safe_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe_name)
    
    # Limit length
    if len(safe_name) > max_length:
        name_part = safe_name[:max_length-4]
        safe_name = name_part + "..."
    
    # Ensure it's not empty
    if not safe_name.strip():
        safe_name = "unnamed_file"
    
    return safe_name.strip()


def copy_with_backup(source, destination, backup_suffix=".bak"):
    """
    Copy a file to destination, creating a backup if destination exists.
    
    Args:
        source: Source file path
        destination: Destination file path
        backup_suffix: Suffix for backup file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            return False
        
        # Create backup if destination exists
        if destination.exists():
            backup_path = destination.with_suffix(destination.suffix + backup_suffix)
            shutil.copy2(str(destination), str(backup_path))
        
        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(str(source), str(destination))
        return True
        
    except Exception:
        return False
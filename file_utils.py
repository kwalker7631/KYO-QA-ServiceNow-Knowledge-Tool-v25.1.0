# file_utils.py
# Version: 25.1.0
# Last modified: 2025-07-02
# Utilities for file operations, including file locking detection and safe copy operations

import os
import sys
import shutil
import time
from pathlib import Path
import logging
from logging_utils import setup_logger, log_info, log_error, log_warning
from datetime import datetime

logger = setup_logger("file_utils")

def ensure_folders(base_folder=None):
    """Create all necessary application folders on startup."""
    from config import LOGS_DIR, OUTPUT_DIR, PDF_TXT_DIR, CACHE_DIR
    
    # List of folders to ensure
    folders = [LOGS_DIR, OUTPUT_DIR, PDF_TXT_DIR, CACHE_DIR]
    
    # Add a "needs_review" subdirectory under PDF_TXT_DIR
    review_dir = PDF_TXT_DIR / "needs_review"
    folders.append(review_dir)
    
    for folder in folders:
        try:
            folder.mkdir(parents=True, exist_ok=True)
            log_info(logger, f"Ensured folder exists: {folder}")
        except Exception as e:
            log_error(logger, f"Failed to create folder {folder}: {e}")

def is_file_locked(filepath):
    """
    Check if a file is locked by another process with improved detection.
    
    Args:
        filepath: Path to the file to check
        
    Returns:
        bool: True if the file is locked, False otherwise
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return False  # File doesn't exist, so it can't be locked

    try:
        # Try both read and write modes to handle different lock types
        # Some applications like Excel can lock in different ways
        
        # First check read access
        with open(filepath, 'r', encoding='utf-8') as f:
            # Try read operations
            f.read(1)
            
        # Then check write access
        with open(filepath, 'a', encoding='utf-8') as f:
            # Attempt to get an exclusive lock
            if sys.platform == 'win32':
                try:
                    import msvcrt
                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except (ImportError, IOError):
                    log_warning(logger, f"File is locked for writing: {filepath}")
                    return True
            else:
                try:
                    import fcntl
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (ImportError, IOError):
                    log_warning(logger, f"File is locked for writing: {filepath}")
                    return True
    except (IOError, PermissionError):
        # File is definitely locked if we can't open it
        log_warning(logger, f"File lock check failed. File is likely open: {filepath}")
        return True

    return False

def cleanup_temp_files(directory=None):
    """
    Removes temporary files from cache and review folders.
    
    Args:
        directory: Optional specific directory to clean
        
    Returns:
        int: Number of files cleaned up
    """
    from config import CACHE_DIR
    
    if directory is None:
        directory = CACHE_DIR
        
    print(f"Cleaning up temporary files in {directory}...")
    count = 0
    
    try:
        if directory.exists():
            # Only delete files older than 24 hours
            now = datetime.now().timestamp()
            
            for item in directory.iterdir():
                try:
                    if item.is_file():
                        file_age = now - item.stat().st_mtime
                        if file_age > 86400:  # 24 hours in seconds
                            item.unlink()
                            count += 1
                    elif item.is_dir():
                        # Recursively clean subdirectories
                        subdir_count = cleanup_temp_files(item)
                        count += subdir_count
                        
                        # Remove empty directories
                        if not any(item.iterdir()):
                            item.rmdir()
                except Exception as e:
                    log_warning(logger, f"Error deleting {item}: {e}")
    except Exception as e:
        log_error(logger, f"Error during cleanup: {e}")
        
    log_info(logger, f"Cleaned up {count} temporary files")
    return count

def open_file(path):
    """
    Opens a file with the default system application.
    
    Args:
        path: Path to the file to open
        
    Returns:
        bool: True if successful, False otherwise
    """
    path = str(path)
    try:
        if hasattr(os, 'startfile'):  # For Windows
            os.startfile(path)
        else:  # For macOS and Linux
            import subprocess
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, path])
        log_info(logger, f"Opened file: {path}")
        return True
    except Exception as e:
        log_error(logger, f"Failed to open file {path}: {e}")
        return False

def copy_file_safely(source_path, dest_path, retries=3, wait_time=1.0):
    """
    Copy a file with enhanced retry mechanism and error handling.
    
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
    
    # If destination exists, check if it's writable first
    if dest_path.exists():
        if is_file_locked(dest_path):
            log_error(logger, f"Destination file is locked: {dest_path}")
            return False
            
        # Backup existing file before overwriting
        try:
            backup_path = dest_path.with_suffix(f"{dest_path.suffix}.bak")
            shutil.copy2(dest_path, backup_path)
            log_info(logger, f"Created backup of existing file: {backup_path}")
        except Exception as e:
            log_warning(logger, f"Could not create backup of {dest_path}: {e}")

    last_error = None
    for attempt in range(retries):
        try:
            # Improved handling for large files
            if source_path.stat().st_size >= 10 * 1024 * 1024:  # 10MB or larger
                # Use chunk-by-chunk copy with a progress tracking option
                copied_bytes = 0
                total_bytes = source_path.stat().st_size
                
                with open(source_path, 'rb') as src, open(dest_path, 'wb') as dst:
                    chunk_size = 1024 * 1024  # 1MB chunks
                    while True:
                        chunk = src.read(chunk_size)
                        if not chunk:
                            break
                        dst.write(chunk)
                        copied_bytes += len(chunk)
                        
                        # Log progress for very large files
                        if total_bytes > 100 * 1024 * 1024 and copied_bytes % (10 * 1024 * 1024) == 0:  # Log every 10MB for files >100MB
                            log_info(logger, f"Copying {source_path.name}: {copied_bytes/total_bytes:.1%} complete")
            else:
                # For smaller files, use direct copy
                shutil.copy2(source_path, dest_path)
                
            # Verify the copy was successful by comparing file sizes
            if dest_path.stat().st_size != source_path.stat().st_size:
                raise IOError(f"File size mismatch after copy: {source_path.stat().st_size} vs {dest_path.stat().st_size}")
                
            log_info(logger, f"Copied {source_path} to {dest_path}")
            return True

        except Exception as e:
            last_error = e
            log_warning(logger, f"Copy attempt {attempt+1}/{retries} failed: {e}")
            
            # Sleep with exponential backoff
            backoff_time = wait_time * (2 ** attempt)
            time.sleep(backoff_time)
            
            # Check if the destination file exists but is incomplete
            if dest_path.exists() and dest_path.stat().st_size < source_path.stat().st_size:
                try:
                    # Remove the incomplete file before retrying
                    dest_path.unlink()
                    log_warning(logger, f"Removed incomplete destination file for retry")
                except Exception as unlink_err:
                    log_warning(logger, f"Could not remove incomplete file: {unlink_err}")

    log_error(logger, f"Failed to copy {source_path} to {dest_path} after {retries} attempts. Last error: {last_error}")
    
    # Try to restore from backup if copy failed and we made a backup
    backup_path = dest_path.with_suffix(f"{dest_path.suffix}.bak")
    if backup_path.exists():
        try:
            shutil.copy2(backup_path, dest_path)
            log_warning(logger, f"Restored destination from backup after failed copy")
        except Exception as restore_err:
            log_error(logger, f"Could not restore from backup: {restore_err}")
            
    return False

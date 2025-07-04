import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import LOGS_DIR

def setup_logger(name: str) -> logging.Logger:
    """Sets up a logger with a rotating file handler and console output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.hasHandlers():
        return logger

    # --- FIX: Ensure the log directory exists before creating a log file. ---
    # The RotatingFileHandler cannot create files in a non-existent directory.
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"CRITICAL: Could not create log directory at {LOGS_DIR}. Error: {e}")
        # Fallback to a simple console logger if file logging fails
        ch = logging.StreamHandler()
        ch_format = logging.Formatter('%(levelname)s - [%(name)s] - %(message)s')
        ch.setFormatter(ch_format)
        logger.addHandler(ch)
        return logger
    # --- END FIX ---

    # Console Handler
    ch = logging.StreamHandler()
    ch_format = logging.Formatter('%(levelname)s - [%(name)s] - %(message)s')
    ch.setFormatter(ch_format)
    logger.addHandler(ch)

    # File Handler
    fh = RotatingFileHandler(LOGS_DIR / f"{name}.log", maxBytes=1024*1024, backupCount=3)
    fh_format = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    fh.setFormatter(fh_format)
    logger.addHandler(fh)
    
    return logger

def log_info(logger, message):
    logger.info(message)

def log_error(logger, message, exc_info=False):
    logger.error(message, exc_info=exc_info)

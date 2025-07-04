import json
import os
import logging
from pathlib import Path  # <-- Import Path
from version import __version__
from branding import KyoceraColors

# Initialize logging
logger = logging.getLogger('config')

# --- Define all pattern variables with default empty values FIRST ---
MODEL_PATTERNS = []
PART_NUMBER_PATTERNS = []
SERIAL_NUMBER_PATTERNS = []
QA_NUMBER_PATTERNS = []
DOCUMENT_TYPE_PATTERNS = []
DOCUMENT_TITLE_PATTERNS = []
REVISION_PATTERNS = []
LANGUAGE_PATTERNS = []
EXCLUSION_PATTERNS = []
UNWANTED_AUTHORS = []
STANDARDIZATION_RULES = {}  # Rules are a dictionary

# --- Now, try to overwrite the defaults with values from custom_patterns.py ---
try:
    from custom_patterns import *
    logging.info("Successfully loaded custom patterns.")
except ImportError as e:
    logging.warning(f"Could not import from custom_patterns.py: {e}. Using default empty patterns.")
except Exception as e:
    logging.error(f"An unexpected error occurred while loading custom patterns: {e}")


# --- FIX: Use Path objects for all directory constants ---
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'output'
LOGS_DIR = BASE_DIR / 'logs'
ASSETS_DIR = BASE_DIR / 'assets'
PDF_TXT_DIR = OUTPUT_DIR / 'pdf_texts'
CACHE_DIR = BASE_DIR / 'cache'
CONFIG_FILE = BASE_DIR / 'config.json'

# --- GUI and App Color Configuration ---
BRAND_COLORS = {
    "background": KyoceraColors.LIGHT_GREY,
    "header": KyoceraColors.DARK_GREY,
    "purple": KyoceraColors.PURPLE,
    "status_review": KyoceraColors.STATUS_ORANGE_LIGHT,
    "status_pass": KyoceraColors.STATUS_GREEN_LIGHT,
    "status_fail": KyoceraColors.STATUS_RED_LIGHT,
    "status_ocr": KyoceraColors.STATUS_BLUE_LIGHT
}

# Column names
STATUS_COLUMN_NAME = "Validation Status"
DESCRIPTION_COLUMN_NAME = "description"
META_COLUMN_NAME = "meta"
AUTHOR_COLUMN_NAME = "author"


# --- Functions for GUI Configuration ---
DEFAULT_CONFIG = {
    'input_dir': '',
    'output_dir': str(OUTPUT_DIR.absolute()), # Store as string in JSON
}

def load_config():
    """
    Loads the configuration from config.json.
    If the file doesn't exist, it creates a default one.
    """
    if not os.path.exists(CONFIG_FILE):
        logger.info(f"Config file not found. Creating default config at {CONFIG_FILE}")
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            logger.info(f"Configuration loaded from {CONFIG_FILE}")
            return config
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading config file: {e}. Using default config.")
        return DEFAULT_CONFIG

def save_config(config_data):
    """
    Saves the given configuration data to config.json.
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
            logger.info(f"Configuration saved to {CONFIG_FILE}")
    except IOError as e:
        logger.error(f"Error saving config file: {e}")

def get_app_version():
    """
    Returns the application version from the version.py file.
    """
    return __version__

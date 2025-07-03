# config.py
from pathlib import Path

# Application directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
PDF_TXT_DIR = BASE_DIR / "review_files"

# Column name for models/metadata in Excel sheet
# This is the column where model information will be stored
# Change this to match an existing column name in your Excel file
# Common options: "Models", "Applicable Models", "Device Models", "Metadata"
META_COLUMN_NAME = "Models"  # Changed from "Applicable Models/Metadata"

# Brand colors
BRAND_COLORS = {
    # Primary colors
    "background": "#F9F9F9",
    "frame_background": "#F2F2F2",
    "kyocera_red": "#CC0033",
    "kyocera_black": "#333333",
    
    # Text colors
    "header_text": "#FFFFFF",
    "body_text": "#444444",
    
    # Accent colors
    "accent_blue": "#0078D7",
    "accent_grey": "#999999",
    
    # Status colors
    "success_green": "#28A745",
    "warning_yellow": "#FFC107",
    "error_red": "#DC3545",
}

# Default processing options
DEFAULT_OPTIONS = {
    "use_ocr": True,
    "auto_open_result": True,
    "cleanup_temp": True,
}
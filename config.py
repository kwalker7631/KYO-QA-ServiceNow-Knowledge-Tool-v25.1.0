# config.py
# Version: 26.0.0 (Repaired)
# Last modified: 2025-07-03
# Central configuration for all application settings.

from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
# Defines all the core folders the application uses.
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
PDF_TXT_DIR = BASE_DIR / "PDF_TXT"
CACHE_DIR = BASE_DIR / ".cache"
# FIXED: Added the missing ASSETS_DIR definition for UI icons.
ASSETS_DIR = BASE_DIR / "assets"

# --- BRANDING AND UI ---
# Defines the color scheme for the modern user interface.
BRAND_COLORS = {
    "kyocera_red": "#DA291C",
    "kyocera_black": "#231F20",
    "background": "#F0F2F5",
    "frame_background": "#FFFFFF",
    "header_text": "#000000",
    "accent_blue": "#0078D4",
    "success_green": "#107C10",
    "warning_orange": "#FFA500",
    "fail_red": "#DA291C",
    "highlight_blue": "#0078D4",
    # Status bar background colors for different states
    "status_default_bg": "#F8F8F8",
    "status_processing_bg": "#DDEEFF",
    "status_ocr_bg": "#E6F7FF",
    "status_ai_bg": "#F9F0FF",
}

# --- EXCEL REPORT CONFIGURATION ---
# Defines the column names to look for in the input Excel file.
STATUS_COLUMN_NAME = "Processing Status"
DESCRIPTION_COLUMN_NAME = "Short description"
META_COLUMN_NAME = "Meta"
AUTHOR_COLUMN_NAME = "Author"


# --- DATA PROCESSING RULES ---
# Patterns to exclude from the results to avoid false positives.
EXCLUSION_PATTERNS = ["CVE-", "CWE-", "TK-"]

# Default regex patterns for finding model numbers.
# Users can add their own in custom_patterns.py
MODEL_PATTERNS = [
    r'\bTASKalfa\s*[\w-]+\b',
    r'\bECOSYS\s*[\w-]+\b',
    r'\bPF-[\w-]+\b',
    r'\bFS-[\w-]+\b',
]

# Default regex patterns for finding QA/Service Bulletin numbers.
QA_NUMBER_PATTERNS = [
    r'\bQA\s*[\d-]+\b',
    r'\bSB\s*[\d-]+\b',
]

# List of author names to ignore (e.g., generic system accounts).
UNWANTED_AUTHORS = ["System", "Admin", "Administrator"]

# Rules to standardize model names (e.g., remove spaces).
STANDARDIZATION_RULES = {
    " ": ""
}

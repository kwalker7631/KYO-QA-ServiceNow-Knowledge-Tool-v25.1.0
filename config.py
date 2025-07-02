# config.py
from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
PDF_TXT_DIR = BASE_DIR / "PDF_TXT"
CACHE_DIR = BASE_DIR / ".cache"
ASSETS_DIR = BASE_DIR / "assets" # For icons

# --- BRANDING AND UI ---
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
    # Status bar background colors
    "status_default_bg": "#F8F8F8",
    "status_processing_bg": "#DDEEFF",
    "status_ocr_bg": "#E6F7FF",
    "status_ai_bg": "#F9F0FF",
}

# --- DATA PROCESSING RULES ---
EXCLUSION_PATTERNS = ["CVE-", "CWE-", "TK-"]
MODEL_PATTERNS = [
    r'\bTASKalfa\s*[\w-]+\b',
    r'\bECOSYS\s*[\w-]+\b',
    r'\b(PF|DF|MK|AK|DP|BF|JS)-\d+[\w-]*\b',
]
QA_NUMBER_PATTERNS = [r'\bQA[-_]?[\w-]+', r'\bSB[-_]?[\w-]+']
UNWANTED_AUTHORS = ["Knowledge Import"]
STANDARDIZATION_RULES = {"TASKalfa-": "TASKalfa ", "ECOSYS-": "ECOSYS "}

# --- EXCEL MAPPING ---
META_COLUMN_NAME = "Meta"
AUTHOR_COLUMN_NAME = "Author"
DESCRIPTION_COLUMN_NAME = "Short description"
STATUS_COLUMN_NAME = "Processing Status"
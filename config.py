# config.py
from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
PDF_TXT_DIR = BASE_DIR / "PDF_TXT"
NEEDS_REVIEW_DIR = PDF_TXT_DIR / "needs_review"
CACHE_DIR = BASE_DIR / ".cache"

# --- BRANDING AND UI ---
BRAND_COLORS = {
    "kyocera_red": "#E30613", "kyocera_black": "#231F20", "background": "#FFFFFF",
    "frame_background": "#F5F5F5", "header_text": "#000000", "accent_blue": "#0A9BCD",
    "success_green": "#00B176", "warning_yellow": "#FFEB9C", "fail_red": "#FFC7CE",
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
# config.py
from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
PDF_TXT_DIR = BASE_DIR / "PDF_TXT"
TESSERACT_DIR = BASE_DIR / "tesseract"

# --- BRANDING AND UI ---
BRAND_COLORS = {
    "kyocera_red": "#E30613",
    "kyocera_black": "#231F20",
    "background": "#FFFFFF",
    "frame_background": "#F5F5F5",
    "header_text": "#000000",
    "accent_blue": "#0A9BCD",
    "success_green": "#00B176",
    "warning_yellow": "#F5B400",
}

# --- Exclusion list for unwanted patterns ---
EXCLUSION_PATTERNS = [
    "CVE-",
    "CWE-",
    "TK-",
]

# --- DATA HARVESTING CONFIGURATION ---
MODEL_PATTERNS = [
    # Pattern for major model lines like TASKalfa and ECOSYS
    r'\bTASKalfa\s*[a-zA-Z0-9-]+\b',
    r'\bECOSYS\s*[a-zA-Z0-9-]+\b',
    
    # Whitelist pattern for known accessory prefixes
    r'\b(PF|DF|MK|AK|DP|BF|JS)-\d+[\w-]*\b',
]

QA_NUMBER_PATTERNS = [
    r'\bQA[-_]?[\w-]+',
    r'\bSB[-_]?[\w-]+',
]

SHORT_QA_PATTERN = r'(\d{5,})'

DATE_PATTERNS = [
    r'(?i)(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}',
    r'\d{1,2}/\d{1,2}/\d{4}',
    r'\d{4}-\d{2}-\d{2}',
]

SUBJECT_PATTERNS = [
    r'(?i)Subject\s*:\s*(.*)',
    r'(?i)Title\s*:\s*(.*)',
    r'SUBJECT\s*–\s*(.*)',
]

APP_SOFTWARE_PATTERNS = [
    r'\bKYOCERA\s*Net\s*Viewer\b',
    r'\bCommand\s*Center\s*RX\b',
]

AUTHOR_PATTERNS = [
    r'(?i)Author\s*:\s*(.*)'
]
UNWANTED_AUTHORS = [
    "Knowledge Import"
]

# --- STANDARDIZATION RULES ---
STANDARDIZATION_RULES = {
    "TASKalfa-": "TASKalfa ",
    "ECOSYS-": "ECOSYS ",
}


# --- EXCEL GENERATION ---
META_COLUMN_NAME = "Meta"

# Column name mapping used for ServiceNow import
HEADER_MAPPING = {
    "active": "Active",
    "article_type": "Article type",
    "author": "Author",
    "category": "Category(category)",
    "configuration_item": "Configuration item",
    "confidence": "Confidence",
    "description": "Description",
    "attachment_link": "Attachment link",
    "disable_commenting": "Disable commenting",
    "disable_suggesting": "Disable suggesting",
    "display_attachments": "Display attachments",
    "flagged": "Flagged",
    "governance": "Governance",
    "kb_category": "Category(kb_category)",
    "knowledge_base": "Knowledge base",
    "meta": "Meta",
    "meta_description": "Meta Description",
    "ownership_group": "Ownership Group",
    "published": "Published",
    "scheduled_publish_date": "Scheduled publish date",
    "short_description": "Short description",
    "article_body": "Article body",
    "topic": "Topic",
    "problem_code": "Problem Code",
    "models": "models",
    "ticket_number": "Ticket#",
    "valid_to": "Valid to",
    "view_as_allowed": "View as allowed",
    "wiki": "Wiki",
    "sys_id": "Sys ID",
    "file_name": "file_name",
    "change_type": "Change Type",
    "revision": "Revision",
    "processing_status": "Processing Status",
}

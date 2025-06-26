# KYO QA ServiceNow Configuration - FINAL VERSION
from version import VERSION

REQUIRED_FOLDERS = ["logs", "output", "PDF_TXT", "temp"]

# This dictionary ensures the data keys always match your template's column names.
HEADER_MAPPING = {
    'active': 'Active', 'article_type': 'Article type', 'author': 'Author',
    'category': 'Category(category)', 'confidence': 'Confidence', 'description': 'Description',
    'disable_commenting': 'Disable commenting', 'disable_suggesting': 'Disable suggesting',
    'display_attachments': 'Display attachments', 'flagged': 'Flagged', 'governance': 'Governance',
    'kb_category': 'Category(kb_category)', 'knowledge_base': 'Knowledge base', 'meta': 'Meta',
    'meta_description': 'Meta Description', 'published_date': 'Published',
    'short_description': 'Short description', 'topic': 'Topic', 'models': 'models',
    'valid_to': 'Valid to', 'change_type': 'Change Type', 'revision': 'Revision',
    'file_name': 'file_name', 'needs_review': 'needs_review', 'processing_status': 'processing_status'
}

QA_NUMBER_PATTERNS = [
    r"Ref\.\s*No\.\s*([A-Z0-9]{2,}[-][0-9]+)\s*\(([A-Z]\d+)\)",
    r"\b([A-Z0-9]{2,}[-][0-9]+)\s*\(([A-Z]\d+)\)",
    r"Ref\.\s*No\.\s*([A-Z0-9]{2,}[-][0-9]+)",
    r"((E\d{3,}|[A-Z0-9]{2,})[-][A-Z0-9]{2,}[-][0-9]+)\b",
    r"([A-Z0-9]{2,}-\d{4})\b"
]
SHORT_QA_PATTERN = r"\(([A-Z]\d+)\)"
MODEL_PATTERNS = [
    r"Model[:\s]*\n*((?:(?:TASKalfa|ECOSYS|FS-C)\s+[A-Za-z0-9\s,/-]+)+)", 
    r"\b((?:TASKalfa|ECOSYS|FS-C)[\sA-Za-z0-9,/-]+)\b",
]
SUBJECT_PATTERNS = [
    r'Subject\s*:\s*([^\n\r]+?)(?:\n\n|Model:|Classification:|timing:|Phenomenon:|Problem:|Cause:|Measure:|Remarks:|$)',
]
CHANGE_TYPE_PATTERNS = [
    r"Type\s+of\s+change[:\s\n]*.*?(Hardware|Firmware\s+and\s+Software|Information)"
]
STANDARDIZATION_RULES = {"default_author": "Knowledge Import"}
# data_harvesters.py
import re
from pathlib import Path
import importlib

# We only import the default patterns here. Custom patterns will be loaded dynamically.
from config import (
    MODEL_PATTERNS as DEFAULT_MODEL_PATTERNS,
    QA_NUMBER_PATTERNS as DEFAULT_QA_PATTERNS,
    SHORT_QA_PATTERN,
    DATE_PATTERNS,
    SUBJECT_PATTERNS,
    STANDARDIZATION_RULES,
    AUTHOR_PATTERNS,
    UNWANTED_AUTHORS,
    EXCLUSION_PATTERNS,
)

from extract.common import clean_text_for_extraction, bulletproof_extraction
from ocr_utils import get_pdf_metadata

#==============================================================
# --- NEW FEATURE: Dynamic Pattern Loading ---
# This function re-reads the custom patterns file every time it's called,
# ensuring the latest user-saved rules are always used.
#==============================================================
def get_combined_patterns(pattern_name: str, default_patterns: list) -> list:
    """
    Loads custom patterns from custom_patterns.py and combines them with defaults.
    This function reloads the module to guarantee the latest version is used.
    """
    custom_patterns = []
    try:
        # Import the module and then force a reload to get the latest version from disk
        import custom_patterns as custom_module
        importlib.reload(custom_module)
        custom_patterns = getattr(custom_module, pattern_name, [])
    except (ImportError, AttributeError):
        # It's okay if the file or list doesn't exist yet.
        pass
    
    # Combine lists, ensuring no duplicates. Custom patterns take precedence.
    return custom_patterns + [p for p in default_patterns if p not in custom_patterns]
#==============================================================
# --- END OF NEW FEATURE ---
#==============================================================

def clean_model_string(model_str: str) -> str:
    for rule, replacement in STANDARDIZATION_RULES.items():
        model_str = model_str.replace(rule, replacement)
    return model_str.strip()

def is_excluded(text: str) -> bool:
    for pattern in EXCLUSION_PATTERNS:
        if pattern.lower() in text.lower():
            return True
    return False

def harvest_models_from_text(text: str) -> set:
    found_models = set()
    # Use the dynamic function to get the latest patterns
    model_patterns_to_use = get_combined_patterns("MODEL_PATTERNS", DEFAULT_MODEL_PATTERNS)
    for pattern in model_patterns_to_use:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if not is_excluded(match):
                cleaned_match = clean_model_string(match)
                found_models.add(cleaned_match)
    return found_models

def harvest_models_from_filename(filename: str) -> set:
    found_models = set()
    # Use the dynamic function to get the latest patterns
    model_patterns_to_use = get_combined_patterns("MODEL_PATTERNS", DEFAULT_MODEL_PATTERNS)
    for pattern in model_patterns_to_use:
        search_text = filename.replace("_", " ")
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            if not is_excluded(match):
                cleaned_match = clean_model_string(match)
                found_models.add(cleaned_match)
    return found_models

def harvest_qa_number(text: str) -> str:
    # Use the dynamic function to get the latest patterns
    qa_patterns_to_use = get_combined_patterns("QA_NUMBER_PATTERNS", DEFAULT_QA_PATTERNS)
    for pattern in qa_patterns_to_use:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""

# ... (The rest of the file remains unchanged)
def harvest_short_qa_number(full_qa_number: str) -> str:
    if full_qa_number:
        match = re.search(SHORT_QA_PATTERN, full_qa_number)
        if match: return match.group(1).strip()
    return ""

def harvest_date(text: str) -> str:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match: return match.group(0).strip()
    return ""

def harvest_subject(text: str) -> str:
    for pattern in SUBJECT_PATTERNS:
        match = re.search(pattern, text)
        if match and match.group(1): return match.group(1).strip()
    return ""

def harvest_author(text: str) -> str:
    for pattern in AUTHOR_PATTERNS:
        match = re.search(pattern, text)
        if match and match.group(1):
            author = match.group(1).strip()
            if author in UNWANTED_AUTHORS: return ""
            return author
    return ""


def harvest_metadata(text: str) -> dict:
    """Extract device models from raw text."""
    models = sorted(harvest_models_from_text(text))
    models_str = ", ".join(models) if models else "Not Found"
    return {"models": models_str}


def ai_extract(text: str, pdf_path: Path) -> dict:
    """High-level extraction helper used by the processing engine."""
    cleaned = clean_text_for_extraction(text)
    result = bulletproof_extraction(cleaned, pdf_path.name)
    meta = harvest_metadata(cleaned)
    result.update(meta)
    result["Meta"] = meta["models"]
    pdf_meta = get_pdf_metadata(pdf_path)
    if pdf_meta.get("author") and not result.get("author"):
        result["author"] = pdf_meta["author"]
    return result

def harvest_all_data(text: str, filename: str) -> dict:
    models_from_text = harvest_models_from_text(text)
    models_from_filename = harvest_models_from_filename(filename)
    all_found_models = sorted(list(models_from_text.union(models_from_filename)))
    full_qa = harvest_qa_number(text)
    short_qa = harvest_short_qa_number(full_qa)
    published_date = harvest_date(text)
    subject = harvest_subject(text)
    author = harvest_author(text)
    desc_parts = [part for part in [full_qa, subject] if part]
    short_description = ", ".join(desc_parts)
    models_str = ", ".join(all_found_models) if all_found_models else "Not Found"
    return {
        "models": models_str, "full_qa_number": full_qa, "short_qa_number": short_qa,
        "published_date": published_date, "subject": subject if subject else "No Subject Found",
        "author": author, "short_description": short_description
    }
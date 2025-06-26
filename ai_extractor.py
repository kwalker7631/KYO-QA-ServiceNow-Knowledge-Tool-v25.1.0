# KYO QA ServiceNow AI Extractor - FINAL VERSION
import re
from logging_utils import setup_logger
from config import STANDARDIZATION_RULES, QA_NUMBER_PATTERNS, SHORT_QA_PATTERN, MODEL_PATTERNS, CHANGE_TYPE_PATTERNS

logger = setup_logger("ai_extractor")

def transform_qa_number(full_qa, short_qa, revision_str):
    full_qa = full_qa.replace('_', '-')
    match = re.match(r"(E\d+)-([A-Z0-9\-]+)", full_qa)
    if match and not short_qa:
        prefix, suffix = match.groups()
        full_qa = f"{suffix.upper()} ({prefix})"
        short_qa = prefix
    elif short_qa and f"({short_qa})" not in full_qa:
        full_qa = f"{full_qa} ({short_qa})"
    if revision_str:
        full_qa = f"{full_qa} {revision_str}"
    return full_qa, short_qa

def clean_text_for_extraction(text):
    text = re.sub(r'\(Page\.\d+/\d+\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(Revised\s+issue\s+\d+\)', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Ref\.\s*No\.', '', text, flags=re.IGNORECASE)
    # ... other cleaning rules
    return text

def extract_revision_from_filename(filename):
    match = re.search(r'[_-]r(ev\.?)?(\d+)', filename, re.IGNORECASE)
    return f"REV: {match.group(2)}" if match else ""

def ai_extract(text, pdf_path):
    from data_harvesters import harvest_metadata, harvest_subject, identify_document_type
    filename = pdf_path.name
    cleaned_text = clean_text_for_extraction(text)
    data = bulletproof_extraction(cleaned_text, filename)
    revision_str = extract_revision_from_filename(filename)
    if data.get('full_qa_number'):
        full, short = transform_qa_number(data.get('full_qa_number', ''), data.get('short_qa_number', ''), revision_str)
        data['full_qa_number'], data['short_qa_number'] = full, short
    data.update(harvest_metadata(cleaned_text, pdf_path))
    data["subject"] = harvest_subject(cleaned_text, data.get('full_qa_number'))
    data["document_type"] = identify_document_type(cleaned_text)
    return data

def bulletproof_extraction(text, filename):
    data = {}
    if 'leaflet' in filename.lower():
        match = re.search(r'(E\d+)', filename)
        if match:
            short_qa = match.group(1)
            data['full_qa_number'], data['short_qa_number'] = f"LEAFLET ({short_qa})", short_qa
    if not data.get('full_qa_number'):
        for pattern in QA_NUMBER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                data['full_qa_number'] = groups[0].strip()
                if len(groups) > 1 and groups[1]: data['short_qa_number'] = groups[1].strip()
                break
    for pattern in MODEL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            data['models'] = re.sub(r'\s+', ' ', match.group(1)).strip(' ,')
            break
    if not data.get('models'): data['models'] = "Not Found"
    data['change_type'] = "N/A"
    for pattern in CHANGE_TYPE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            change_type = next((group for group in match.groups() if group), None)
            if change_type: data['change_type'] = change_type.replace("and Software", "").strip()
            break
    return data
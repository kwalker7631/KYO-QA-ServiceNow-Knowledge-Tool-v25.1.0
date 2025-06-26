# KYO QA ServiceNow AI Extractor - FINAL VERSION
import re
from logging_utils import setup_logger
from extract.common import clean_text_for_extraction, bulletproof_extraction

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

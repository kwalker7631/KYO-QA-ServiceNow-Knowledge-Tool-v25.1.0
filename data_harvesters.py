# KYO QA ServiceNow AI Extractor - FINAL INTELLIGENT VERSION
import re
from logging_utils import setup_logger, log_info, log_error, log_warning
from config import (
    STANDARDIZATION_RULES,
    QA_NUMBER_PATTERNS,
    SHORT_QA_PATTERN,
    MODEL_PATTERNS,
    DATE_PATTERNS,
    SUBJECT_PATTERNS,
    APP_SOFTWARE_PATTERNS,
)

logger = setup_logger("ai_extractor")


def clean_text_for_extraction(text: str) -> str:
    """Remove common headers/footers and excess whitespace."""
    text = re.sub(r"\(Page\.\d+/\d+\)", "", text)
    text = re.sub(r"Service\s+Bulletin\s+Ref\.", "Ref.", text, flags=re.IGNORECASE)
    text = re.sub(r"For\s+authorized\s+KYOCERA\s+engineers\s+only\.", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Do\s+not\s+distribute\s+to\s+non-authorized\s+parties\.", "", text, flags=re.IGNORECASE)
    text = re.sub(r"CONFIDENTIAL", "", text, flags=re.IGNORECASE)
    text = re.sub(r"KYOCERA\s+Document\s+Solutions\s+Inc\.", "", text, flags=re.IGNORECASE)
    text = re.sub(r"A\s+B\s+C", "", text)
    text = re.sub(r"[\t ]+", " ", text)
    return text


def ai_extract(text: str, pdf_path):
    """High level extraction wrapper used by the processing engine."""
    from data_harvesters import harvest_metadata, harvest_subject, identify_document_type

    try:
        filename = pdf_path.name
        log_info(logger, f"Starting intelligent extraction for: {filename}")

        cleaned_text = clean_text_for_extraction(text)
        data = bulletproof_extraction(cleaned_text, filename)

        supplemental_data = harvest_metadata(cleaned_text, pdf_path)
        data["published_date"] = data.get("published_date") or supplemental_data.get("published_date", "")
        data["author"] = data.get("author") or supplemental_data.get("author", STANDARDIZATION_RULES["default_author"])

        data["subject"] = harvest_subject(cleaned_text, data.get("full_qa_number"))
        data["document_type"] = identify_document_type(cleaned_text)

        if data.get("models") and data["models"] != "Not Found":
            data["Meta"] = ", ".join([m.strip() for m in data["models"].split(",")])

        log_info(
            logger,
            f"Final Data for {filename}: QA='{data.get('full_qa_number')}', "
            f"Short QA='{data.get('short_qa_number')}', Models='{data.get('models', '')[:70]}...'",
        )
        return data
    except Exception as e:  # pragma: no cover - safety net
        log_error(logger, f"Critical error in ai_extract for {pdf_path.name}: {e}")
        return create_error_data(pdf_path.name)


def create_error_data(filename: str) -> dict:
    """Return a standardized record for processing errors."""
    return {
        "full_qa_number": "",
        "short_qa_number": "",
        "models": "Extraction Error",
        "subject": f"Error processing {filename}",
        "author": STANDARDIZATION_RULES.get("default_author", "System"),
        "published_date": "",
        "document_type": "Unknown",
        "needs_review": True,
        "Meta": "",
    }


def bulletproof_extraction(text: str, filename: str) -> dict:
    """Extract QA numbers and models using multiple fallbacks."""
    data = {"full_qa_number": None, "short_qa_number": None}

    search_targets = [text, filename]
    for target in search_targets:
        if data.get("full_qa_number"):
            break
        for pattern in QA_NUMBER_PATTERNS:
            match = re.search(pattern, target, re.IGNORECASE)
            if match:
                if pattern == r"\b(E\d+)-([A-Z0-9]{2,}[-][0-9A-Z]+)\b":
                    data["short_qa_number"] = match.group(1).strip()
                    data["full_qa_number"] = match.group(2).strip()
                    log_info(logger, f"QA Number extracted from '{target[:30]}...' using E-number pattern.")
                elif len(match.groups()) > 1 and match.group(2):
                    data["full_qa_number"] = match.group(1).strip()
                    data["short_qa_number"] = match.group(2).strip()
                    log_info(logger, f"QA Number extracted from '{target[:30]}...' using P-number pattern.")
                else:
                    data["full_qa_number"] = match.group(1).strip()
                    short_match = re.search(SHORT_QA_PATTERN, target, re.IGNORECASE)
                    if short_match:
                        data["short_qa_number"] = short_match.group(1)
                    log_info(logger, f"QA Number extracted from '{target[:30]}...' using general pattern.")
                break
        if data.get("full_qa_number"):
            break

    for pattern in MODEL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            models_text = re.sub(r"\s+", " ", match.group(1)).strip(" ,-")
            data["models"] = models_text
            log_info(logger, f"Extracted models: {models_text[:100]}...")
            break

    if not data.get("models"):
        data["models"] = "Not Found"

    return data


def harvest_subject(text: str, qa_number: str | None = None) -> str:
    """Extract a clean subject, removing the QA number if present."""
    subject = "No subject found"
    for pattern in SUBJECT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            subject = match.group(1).strip()
            subject = re.sub(r"\s+", " ", subject)
            if qa_number and qa_number in subject:
                subject = subject.replace(qa_number, "").strip(" -")
            max_len = STANDARDIZATION_RULES.get("max_subject_length", 250)
            if len(subject) > max_len:
                subject = subject[:max_len].rsplit(" ", 1)[0] + "..."
            break
    return subject


def harvest_metadata(text: str, pdf_path=None) -> dict:
    """Extract supplemental metadata like dates and authors."""
    from ocr_utils import get_pdf_metadata

    pdf_metadata = get_pdf_metadata(pdf_path) if pdf_path else {}
    results = {"published_date": "", "author": STANDARDIZATION_RULES["default_author"]}
    for pattern in DATE_PATTERNS:
        pub_regex = rf"(?:published|issue(?:d)?|publication|revision\s*date)[^\n:]*[:\s]*({pattern})"
        pub_match = re.search(pub_regex, text, re.IGNORECASE)
        if pub_match:
            results["published_date"] = pub_match.group(1)
            break
    if not results.get("published_date"):
        for key in ("modDate", "creationDate"):
            if pdf_metadata.get(key):
                results["published_date"] = pdf_metadata[key]
                break
    author_match = re.search(r"\b(?:author|created\s+by):?\s*([A-Za-z\s]+)(?:\n|$)", text, re.IGNORECASE)
    if author_match:
        results["author"] = author_match.group(1).strip()
    elif pdf_metadata.get("author"):
        results["author"] = pdf_metadata["author"]
    return results


def identify_document_type(text: str) -> str:
    """Identify the document type from its content."""
    text_lower = text.lower()
    if re.search(r"\bservice\s+bulletin\b", text_lower):
        return "Service Bulletin"
    if re.search(r"\b(?:qa|quality\s+assurance)\b", text_lower):
        return "Quality Assurance"
    if re.search(r"\btechnical\s+(?:bulletin|note)\b", text_lower):
        return "Technical Bulletin"
    if re.search(APP_SOFTWARE_PATTERNS["keywords"], text_lower, re.IGNORECASE):
        return "Software Bulletin"
    return "Unknown"

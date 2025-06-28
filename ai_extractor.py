"""Extraction entry points for QA knowledge tool."""


from logging_utils import setup_logger, log_info, log_error
from config import (
    STANDARDIZATION_RULES,
    DATE_PATTERNS,
    SUBJECT_PATTERNS,
    APP_SOFTWARE_PATTERNS,
)
from data_harvesters import (
    harvest_metadata,
    harvest_subject,
    identify_document_type,
)
from extract.common import (
    bulletproof_extraction,
    clean_text_for_extraction,
)

logger = setup_logger("ai_extractor")

__all__ = [
    "ai_extract",
    "bulletproof_extraction",
    "harvest_metadata",
    "harvest_subject",
    "identify_document_type",
    "STANDARDIZATION_RULES",
    "DATE_PATTERNS",
    "SUBJECT_PATTERNS",
    "APP_SOFTWARE_PATTERNS",
]


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


def ai_extract(text: str, pdf_path):
    """High level extraction wrapper used by the processing engine."""
    try:
        filename = pdf_path.name
        log_info(logger, f"Starting intelligent extraction for: {filename}")

        cleaned_text = clean_text_for_extraction(text)
        data = bulletproof_extraction(cleaned_text, filename)

        supplemental_data = harvest_metadata(cleaned_text, pdf_path)
        data["published_date"] = data.get("published_date") or supplemental_data.get("published_date", "")
        data["author"] = data.get("author") or supplemental_data.get("author", STANDARDIZATION_RULES["default_author"])
        if (not data.get("models") or data["models"] == "Not Found") and supplemental_data.get("models"):
            data["models"] = supplemental_data["models"]

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

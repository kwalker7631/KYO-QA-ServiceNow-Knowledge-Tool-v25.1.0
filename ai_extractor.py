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

import data_harvesters

logger = setup_logger("gui")


def ai_extract(text: str, pdf_path):
    """Proxy to :func:`data_harvesters.ai_extract`. Any caller can monkeypatch
    ``data_harvesters.harvest_metadata`` before invoking this helper to adjust
    metadata extraction."""

    return data_harvesters.ai_extract(text, pdf_path)

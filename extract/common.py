import re
from logging_utils import setup_logger, log_info
from config import QA_NUMBER_PATTERNS, SHORT_QA_PATTERN, MODEL_PATTERNS

logger = setup_logger("extract_common")


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


def bulletproof_extraction(text: str, filename: str) -> dict:
    """Extract QA numbers and models using multiple fallbacks."""
    data: dict[str, str | None] = {"full_qa_number": None, "short_qa_number": None}

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

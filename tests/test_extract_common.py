import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from extract.common import clean_text_for_extraction, bulletproof_extraction


def test_clean_and_extract_basic():
    raw = "CONFIDENTIAL Ref. No. ABC-123 (E456)"
    cleaned = clean_text_for_extraction(raw)
    assert "CONFIDENTIAL" not in cleaned
    data = bulletproof_extraction(cleaned, "dummy.pdf")
    assert data["full_qa_number"] == "ABC-123"
    assert data["short_qa_number"] == "E456"

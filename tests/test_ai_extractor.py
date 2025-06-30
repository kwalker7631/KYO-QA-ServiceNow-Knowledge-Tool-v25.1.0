import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import ai_extractor


def test_ai_extract_basic(monkeypatch):
    sample_text = (
        "Service Bulletin\n"
        "Subject: Replace fuse\n"
        "Ref. No. AB-1234 (E22)\n"
        "Model:\nTASKalfa 3005i\n"
    )

    monkeypatch.setattr(
        "data_harvesters.harvest_metadata",
        lambda *a, **k: {
            "published_date": "2024-01-01",
            "author": "Tester",
            "models": "TASKalfa 3005i",
        },
    )
    monkeypatch.setattr("ocr_utils.get_pdf_metadata", lambda *_: {})

    monkeypatch.setattr(
        "data_harvesters.bulletproof_extraction",
        lambda *a, **k: {
            "full_qa_number": "AB-1234",
            "short_qa_number": "E22",
            "models": "TASKalfa 3005i",
            "document_type": "Service Bulletin",
        },
    )

    result = ai_extractor.ai_extract(sample_text, Path("file.pdf"))

    assert result["full_qa_number"] == "AB-1234"
    assert result.get("short_qa_number") == "E22"
    assert result["models"] == "TASKalfa 3005i"
    assert result["author"] == "Tester"
    assert result["published_date"] == "2024-01-01"
    assert result["document_type"] == "Service Bulletin"


def test_reexport_functions():
    from extract.common import bulletproof_extraction as common_bp

    # bulletproof_extraction should be re-exported directly
    assert ai_extractor.bulletproof_extraction is common_bp

    # ai_extract should remain callable
    assert callable(ai_extractor.ai_extract)


def test_public_api_contains_bulletproof():
    """Ensure ai_extractor.__all__ exposes bulletproof_extraction."""
    assert "bulletproof_extraction" in ai_extractor.__all__

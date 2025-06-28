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

    monkeypatch.setattr("data_harvesters.harvest_metadata", lambda *a, **k: {
        "published_date": "2024-01-01",
        "author": "Tester",
    })

    result = ai_extractor.ai_extract(sample_text, Path("file.pdf"))

    assert result["full_qa_number"] == "AB-1234"
    assert result.get("short_qa_number") == "E22"
    assert result["models"] == "TASKalfa 3005i"
    assert result["author"] == "Tester"
    assert result["published_date"] == "2024-01-01"
    assert result["document_type"] == "Service Bulletin"


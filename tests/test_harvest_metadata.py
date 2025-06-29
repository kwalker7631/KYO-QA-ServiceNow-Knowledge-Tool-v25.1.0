import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_harvesters import harvest_metadata, ai_extract


def test_harvest_metadata_finds_models(monkeypatch):
    text = "Model:\nTASKalfa 1230i"
    monkeypatch.setattr('data_harvesters.get_combined_patterns', lambda n, d: d)
    result = harvest_metadata(text)
    assert result["models"] == "TASKalfa 1230i"
    assert result["full_qa_number"] == ""


def test_harvest_metadata_includes_qa_numbers():
    text = "Ref. No. AB-1234 (E22)\nModel:\nTASKalfa 2550ci"
    result = harvest_metadata(text)
    assert result["full_qa_number"] == "AB-1234"
    assert result["short_qa_number"] == "E22"


def test_ai_extract_uses_metadata_models(monkeypatch, tmp_path):
    monkeypatch.setattr(
        'data_harvesters.bulletproof_extraction',
        lambda text, filename: {"full_qa_number": "", "short_qa_number": "", "models": "Not Found"}
    )
    monkeypatch.setattr('data_harvesters.harvest_subject', lambda t, q: "sub")
    monkeypatch.setattr('ocr_utils.get_pdf_metadata', lambda p: {})
    monkeypatch.setattr('data_harvesters.get_combined_patterns', lambda n, d: d)

    text = "Model:\nECOSYS M3040"
    pdf_path = tmp_path / "file.pdf"
    pdf_path.write_text("dummy")
    result = ai_extract(text, pdf_path)
    assert result["models"] == "ECOSYS M3040"
    assert result["Meta"] == "ECOSYS M3040"

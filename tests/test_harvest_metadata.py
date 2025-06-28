import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from data_harvesters import harvest_metadata, ai_extract


def test_harvest_metadata_finds_models():
    text = "Model:\nTASKalfa 1230i"
    result = harvest_metadata(text)
    assert result["models"] == "TASKalfa 1230i"


def test_ai_extract_uses_metadata_models(monkeypatch, tmp_path):
    monkeypatch.setattr(
        'extract.common.bulletproof_extraction',
        lambda text, filename: {"full_qa_number": "", "short_qa_number": "", "models": "Not Found"}
    )
    monkeypatch.setattr('data_harvesters.harvest_subject', lambda t, q: "sub")
    monkeypatch.setattr('data_harvesters.identify_document_type', lambda t: "type")
    monkeypatch.setattr('ocr_utils.get_pdf_metadata', lambda p: {})

    text = "Model:\nECOSYS M3040"
    pdf_path = tmp_path / "file.pdf"
    pdf_path.write_text("dummy")
    result = ai_extract(text, pdf_path)
    assert result["models"] == "ECOSYS M3040"
    assert result["Meta"] == "ECOSYS M3040"

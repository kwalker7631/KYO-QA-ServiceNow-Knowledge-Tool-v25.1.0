import sys
from pathlib import Path
import types

# Ensure repository root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import debug_harvester

def test_debug_harvester_uses_new_harvester(monkeypatch, capsys, tmp_path):
    # Fake text extraction
    monkeypatch.setattr(debug_harvester, "extract_text_from_pdf", lambda p: "Model: TASKalfa 4002i")
    # Capture call to harvest_all_data
    called = {}
    def fake_harvest(text, filename):
        called['text'] = text
        called['filename'] = filename
        return {"models": "TASKalfa 4002i"}
    monkeypatch.setattr(debug_harvester, "harvest_all_data", fake_harvest)

    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy")

    debug_harvester.test_model_extraction(pdf_file)
    out = capsys.readouterr().out

    assert called['filename'] == "test.pdf"
    assert "SUCCESS" in out

from pathlib import Path

import data_harvesters

def test_bulletproof_extraction_passes_filename(monkeypatch):
    called = {}
    def fake_harvest(text, filename):
        called['args'] = (text, filename)
        return {'ok': True}
    monkeypatch.setattr(data_harvesters, 'harvest_all_data', fake_harvest)
    result = data_harvesters.bulletproof_extraction('data', Path('docs/file.pdf'))
    assert called['args'][1] == 'file.pdf'
    assert result == {'ok': True}

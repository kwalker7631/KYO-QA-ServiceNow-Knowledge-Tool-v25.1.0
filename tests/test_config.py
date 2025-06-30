import importlib
from pathlib import Path

import config
from file_utils import ensure_folders

def test_needs_review_dir(tmp_path, monkeypatch):
    # Use a temporary base path for folder creation
    monkeypatch.chdir(tmp_path)
    ensure_folders(tmp_path)
    review_dir = tmp_path / 'PDF_TXT' / 'needs_review'
    assert review_dir.exists()
    # also confirm constant path resolves correctly
    importlib.reload(config)
    expected = Path(config.PDF_TXT_DIR / 'needs_review')
    assert expected.name == 'needs_review'


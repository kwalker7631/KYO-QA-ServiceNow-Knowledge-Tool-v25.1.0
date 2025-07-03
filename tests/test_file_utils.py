import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from file_utils import is_file_locked, ensure_folders


def test_is_file_locked(tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("sample")

    # file not locked
    assert not is_file_locked(test_file)


def test_is_file_locked_true(tmp_path: Path):
    locked_file = tmp_path / "locked.txt"
    locked_file.write_text("sample")

    import fcntl
    with open(locked_file, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert is_file_locked(locked_file)
        fcntl.flock(f, fcntl.LOCK_UN)


def test_ensure_folders_creates_review_subdir(tmp_path: Path, monkeypatch):
    monkeypatch.setattr('config.LOGS_DIR', tmp_path / 'logs')
    monkeypatch.setattr('config.OUTPUT_DIR', tmp_path / 'output')
    monkeypatch.setattr('config.CACHE_DIR', tmp_path / '.cache')
    review_dir = tmp_path / 'NEED_REVIEW' / 'needs_review'
    monkeypatch.setattr('config.NEED_REVIEW_DIR', review_dir.parent)
    monkeypatch.setattr('config.OCR_FAILED_DIR', tmp_path / 'OCR_FAILED')
    monkeypatch.setattr('config.PDF_TXT_DIR', review_dir.parent)

    ensure_folders()
    assert review_dir.exists()


def test_ensure_folders_renames_pdf_txt(tmp_path: Path, monkeypatch):
    old_dir = tmp_path / 'PDF_TXT'
    old_dir.mkdir()
    monkeypatch.setattr('config.NEED_REVIEW_DIR', tmp_path / 'NEED_REVIEW')
    monkeypatch.setattr('config.OCR_FAILED_DIR', tmp_path / 'OCR_FAILED')
    monkeypatch.setattr('config.PDF_TXT_DIR', tmp_path / 'NEED_REVIEW')
    monkeypatch.setattr('config.LOGS_DIR', tmp_path / 'logs')
    monkeypatch.setattr('config.OUTPUT_DIR', tmp_path / 'output')
    monkeypatch.setattr('config.CACHE_DIR', tmp_path / '.cache')

    ensure_folders()
    assert not old_dir.exists()
    assert (tmp_path / 'NEED_REVIEW').exists()



import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import file_utils


def test_is_file_locked_missing_file(tmp_path):
    missing = tmp_path / "missing.txt"
    assert file_utils.is_file_locked(missing) is False


def test_copy_file_safely(tmp_path):
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    src.write_text("data")
    assert file_utils.copy_file_safely(src, dst)
    assert dst.read_text() == "data"


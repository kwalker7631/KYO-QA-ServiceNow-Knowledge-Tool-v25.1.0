import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from file_utils import is_file_locked


def test_is_file_locked(tmp_path: Path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("sample")

    # file not locked
    assert not is_file_locked(test_file)


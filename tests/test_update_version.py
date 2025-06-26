import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from update_version import FILES_TO_UPDATE


def test_files_list_includes_start_bat():
    assert "START.bat" in FILES_TO_UPDATE
    assert "run_tool.bat" not in FILES_TO_UPDATE


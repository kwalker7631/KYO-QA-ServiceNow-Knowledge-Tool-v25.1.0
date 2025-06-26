import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import file_utils
import config


def test_ensure_folders_uses_config(tmp_path, monkeypatch):
    test_dirs = ["one", "two"]
    monkeypatch.setattr(config, "REQUIRED_FOLDERS", test_dirs, raising=False)
    base = tmp_path / "base"
    file_utils.ensure_folders(base_folder=base)
    for name in test_dirs:
        assert (base / name).exists()

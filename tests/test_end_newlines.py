from pathlib import Path

FILES = [
    "logging_utils.py",
    "config.py",
    "custom_exceptions.py",
    "README.md",
    "requirements.txt",
]


def test_files_end_with_newline():
    repo_root = Path(__file__).resolve().parents[1]
    for name in FILES:
        with open(repo_root / name, "rb") as f:
            f.seek(-1, 2)
            assert f.read() == b"\n", f"{name} does not end with newline"

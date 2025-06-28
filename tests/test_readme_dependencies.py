from pathlib import Path


def test_readme_mentions_dependencies():
    text = Path(__file__).resolve().parents[1].joinpath('README.md').read_text()
    assert 'PyMuPDF' in text and 'PySide6' in text

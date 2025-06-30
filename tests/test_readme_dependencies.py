from pathlib import Path


def test_readme_mentions_dependencies():
    text = Path(__file__).resolve().parents[1].joinpath('README.md').read_text()
    for dep in ['PyMuPDF', 'PySide6', 'Pillow', 'ollama']:
        assert dep in text

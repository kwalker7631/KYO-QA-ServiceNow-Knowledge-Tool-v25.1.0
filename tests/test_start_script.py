from pathlib import Path


def test_start_bat_points_to_run():
    content = Path('START.bat').read_text(encoding='utf-8').lower()
    assert 'python run.py' in content
    assert 'updated_run.py' not in content


def test_docs_reference_run():
    docs = [
        'README.md',
        'updated_readme.md',
        'updated_readme_v25_1_1.md',
        'usage_instructions.md',
    ]
    for doc in docs:
        text = Path(doc).read_text(encoding='utf-8').lower()
        assert 'python run.py' in text
        assert 'updated_run.py' not in text


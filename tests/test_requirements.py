import pathlib


def test_no_ollama_extract_in_requirements():
    reqs = pathlib.Path('requirements.txt').read_text().splitlines()
    assert all('ollama' not in line for line in reqs)
    assert all('extract' not in line for line in reqs)

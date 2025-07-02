import translation_utils
from translation_utils import auto_translate_text


def test_auto_translate_no_lib(monkeypatch):
    monkeypatch.setattr(translation_utils, '_get_translator', lambda: None)
    text = 'hola'
    assert auto_translate_text(text) == text


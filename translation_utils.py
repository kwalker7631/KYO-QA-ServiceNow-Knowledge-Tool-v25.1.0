import importlib
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_translator():
    """Return googletrans Translator instance if available."""
    try:
        gt = importlib.import_module('googletrans')
        return gt.Translator()
    except Exception:
        return None


def auto_translate_text(text: str, target_lang: str = 'en') -> str | None:
    """Translate text to English if translator available.

    Returns translated text, original text if translation not needed or library
    missing, or None if translation failed.
    """
    translator = _get_translator()
    if translator is None:
        return text
    try:
        detected = translator.detect(text).lang
        if detected == target_lang or detected not in {'ja', 'es', 'de'}:
            return text
        result = translator.translate(text, dest=target_lang)
        return result.text
    except Exception:
        return None


import sys

def test_import_without_anthropic(monkeypatch):
    monkeypatch.setitem(sys.modules, 'anthropic', None)
    import importlib
    import error_reporter
    importlib.reload(error_reporter)
    assert hasattr(error_reporter, 'extract_snippet')

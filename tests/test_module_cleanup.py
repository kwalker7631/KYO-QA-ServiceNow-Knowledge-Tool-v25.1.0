import importlib
import inspect
import sys


def test_ai_extractor_has_no_gui_classes():
    ai_extractor = importlib.import_module('ai_extractor')
    class_names = [name for name, _ in inspect.getmembers(ai_extractor, inspect.isclass)]
    assert 'QAApp' not in class_names
    assert 'Worker' not in class_names


def test_gui_components_no_processing_engine_imports():
    if 'gui_components' in sys.modules:
        del sys.modules['gui_components']
    mod = importlib.import_module('gui_components')
    assert 'process_folder' not in mod.__dict__
    assert 'process_zip_archive' not in mod.__dict__

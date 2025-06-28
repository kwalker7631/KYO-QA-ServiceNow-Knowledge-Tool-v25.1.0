import sys
import types
from pathlib import Path
import inspect

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub heavy dependencies if missing
for mod in ('pandas', 'fitz'):
    if mod not in sys.modules:
        sys.modules[mod] = types.ModuleType(mod)
# Stub minimal PySide6 for ai_extractor import
if 'PySide6' not in sys.modules:
    pyside6 = types.ModuleType('PySide6')
    qtwidgets = types.ModuleType('PySide6.QtWidgets')
    qtcore = types.ModuleType('PySide6.QtCore')
    for attr in ['QApplication','QMainWindow','QWidget','QVBoxLayout','QLabel','QPushButton','QFileDialog','QProgressBar','QTextEdit','QMessageBox','QHBoxLayout','QGroupBox']:
        setattr(qtwidgets, attr, object)
    qtcore.QThread = object
    class DummySignal:
        def __init__(self, *a, **k):
            pass
    qtcore.Signal = DummySignal
    qtcore.Qt = types.SimpleNamespace()
    pyside6.QtWidgets = qtwidgets
    pyside6.QtCore = qtcore
    sys.modules['PySide6'] = pyside6
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtCore'] = qtcore
# Stub ai_extractor to avoid circular import
if 'ai_extractor' not in sys.modules:
    ai_extractor = types.ModuleType('ai_extractor')
    ai_extractor.ai_extract = lambda text, path: {}
    sys.modules['ai_extractor'] = ai_extractor
if 'dateutil' not in sys.modules:
    dateutil = types.ModuleType('dateutil')
    sys.modules['dateutil'] = dateutil
if 'dateutil.relativedelta' not in sys.modules:
    rd = types.ModuleType('dateutil.relativedelta')
    class _RD:
        def __init__(self, **kw):
            pass
    rd.relativedelta = _RD
    sys.modules['dateutil.relativedelta'] = rd

import processing_engine


def test_process_folder_signature():
    sig = inspect.signature(processing_engine.process_folder)
    assert 'kb_filepath' in sig.parameters
    assert 'progress_cb' in sig.parameters
    assert 'status_cb' in sig.parameters


def test_process_zip_archive_signature():
    sig = inspect.signature(processing_engine.process_zip_archive)
    assert 'kb_filepath' in sig.parameters
    assert 'progress_cb' in sig.parameters
    assert 'status_cb' in sig.parameters

import sys
import types
from pathlib import Path

# Ensure project root is on the path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub minimal PySide6 if not available
if 'PySide6' not in sys.modules:
    pyside6 = types.ModuleType('PySide6')
    qtcore = types.ModuleType('PySide6.QtCore')
    qtwidgets = types.ModuleType('PySide6.QtWidgets')
    qtgui = types.ModuleType('PySide6.QtGui')

    class Signal:
        def __init__(self, *a, **k):
            pass
        def emit(self, *a, **k):
            pass
        def connect(self, *a, **k):
            pass

    class QThread:
        def __init__(self, *a, **k):
            pass

    qtcore.Signal = Signal
    qtcore.QThread = QThread
    qtcore.Qt = types.SimpleNamespace(WaitCursor=0, ArrowCursor=1)

    # Minimal QtGui stub
    qtgui.QCursor = type('QCursor', (), {})

    # Minimal widget stubs to satisfy imports
    attrs = ['QApplication', 'QMainWindow', 'QWidget', 'QVBoxLayout', 'QLabel',
             'QPushButton', 'QFileDialog', 'QProgressBar', 'QTextEdit',
             'QMessageBox', 'QHBoxLayout', 'QGroupBox']
    for name in attrs:
        setattr(qtwidgets, name, type(name, (), {}))

    pyside6.QtCore = qtcore
    pyside6.QtWidgets = qtwidgets
    pyside6.QtGui = qtgui
    sys.modules['PySide6'] = pyside6
    sys.modules['PySide6.QtCore'] = qtcore
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtGui'] = qtgui

from kyo_qa_tool_app import Worker, logger

def test_worker_exception_logs_and_signals(monkeypatch):
    events = []

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setitem(
        sys.modules,
        'processing_engine',
        types.SimpleNamespace(run_processing_job=boom)
    )

    logged = {}
    def fake_exc(msg, exc_info=None):
        logged['called'] = True
        logged['msg'] = msg
    monkeypatch.setattr(logger, 'exception', fake_exc)

    w = Worker('path', 'kb')
    w.update_status = types.SimpleNamespace(emit=lambda m: events.append(('status', m)))
    w.finished = types.SimpleNamespace(emit=lambda m: events.append(('finished', m)))
    w.update_progress = types.SimpleNamespace(emit=lambda v: None)

    w.run()

    assert logged.get('called')
    assert ('status', 'Error: boom') in events
    assert ('finished', 'Error: boom') in events

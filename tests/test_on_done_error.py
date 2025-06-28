import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Minimal PySide6 stubs
if 'PySide6' not in sys.modules:
    pyside6 = types.ModuleType('PySide6')
    qtwidgets = types.ModuleType('PySide6.QtWidgets')
    qtcore = types.ModuleType('PySide6.QtCore')
    qtgui = types.ModuleType('PySide6.QtGui')

    class DummyButton:
        def __init__(self):
            self.enabled = False
        def setEnabled(self, val):
            self.enabled = val
        def isEnabled(self):
            return self.enabled
    class QApplication: pass
    class QMainWindow: pass
    qtwidgets.QApplication = QApplication
    qtwidgets.QMainWindow = QMainWindow
    qtwidgets.QWidget = object
    qtwidgets.QGroupBox = qtwidgets.QFileDialog = qtwidgets.QProgressBar = object
    qtwidgets.QVBoxLayout = qtwidgets.QHBoxLayout = object
    qtwidgets.QPushButton = qtwidgets.QLabel = object
    qtwidgets.QTextEdit = object
    qtwidgets.QMessageBox = types.SimpleNamespace(critical=lambda *a, **k: None)

    qtcore.Signal = lambda *a, **k: None
    qtcore.QThread = type('QThread', (), {})
    qtcore.Qt = types.SimpleNamespace(ArrowCursor=0)

    class QCursor:
        def __init__(self, *args, **kwargs):
            pass
    qtgui.QCursor = QCursor

    sys.modules['PySide6'] = pyside6
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtCore'] = qtcore
    sys.modules['PySide6.QtGui'] = qtgui

from kyo_qa_tool_app import QAApp


def test_on_done_handles_error_message():
    dummy = types.SimpleNamespace()
    dummy.setCursor = lambda *a, **k: None
    dummy.folder_btn = DummyButton()
    dummy.zip_btn = DummyButton()
    dummy.excel_btn = DummyButton()
    dummy.start_btn = DummyButton()
    logged = {}
    dummy.log = lambda msg: logged.setdefault('msg', msg)
    dialog_shown = {}
    dummy.show_error = lambda title, msg: dialog_shown.setdefault('called', True)

    method = QAApp.on_done.__get__(dummy, type(dummy))
    method('Error: boom')

    assert dialog_shown.get('called')
    assert dummy.start_btn.isEnabled()

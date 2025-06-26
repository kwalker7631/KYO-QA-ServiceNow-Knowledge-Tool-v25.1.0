import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

# Provide minimal PySide6 stubs if the real library is unavailable
if 'PySide6' not in sys.modules:
    pyside6 = types.ModuleType('PySide6')
    qtwidgets = types.ModuleType('PySide6.QtWidgets')
    qtcore = types.ModuleType('PySide6.QtCore')

    class QLabel:
        def __init__(self, text=""):
            self._text = text
        def setText(self, text):
            self._text = text
        def text(self):
            return self._text
    class QTextEdit:
        def __init__(self):
            self._text = []
        def append(self, text):
            self._text.append(text)
        def clear(self):
            self._text = []
        def toPlainText(self):
            return "\n".join(self._text)

    # simple placeholders
    class QApplication:
        pass
    class QMainWindow:  # noqa: D401
        """Dummy base class"""
        pass

    qtwidgets.QApplication = QApplication
    qtwidgets.QMainWindow = QMainWindow
    qtwidgets.QWidget = object
    qtwidgets.QFrame = object
    qtwidgets.QVBoxLayout = qtwidgets.QHBoxLayout = qtwidgets.QGridLayout = object
    qtwidgets.QLabel = QLabel
    qtwidgets.QStatusBar = qtwidgets.QGroupBox = qtwidgets.QLineEdit = qtwidgets.QPushButton = object
    qtwidgets.QFileDialog = qtwidgets.QProgressBar = object
    qtwidgets.QTextEdit = QTextEdit
    qtwidgets.QMessageBox = types.SimpleNamespace(Yes=1, question=lambda *a, **k:1, critical=lambda *a, **k:None, warning=lambda *a, **k:None)

    class Signal:
        def __init__(self, *a, **k):
            pass
        def connect(self, *a, **k):
            pass
    class QTimer:
        def __init__(self, *a, **k):
            pass
        def start(self, *a, **k):
            pass
        def stop(self):
            pass
    class QThread:
        def __init__(self):
            pass
        def start(self):
            pass
        def isRunning(self):
            return False
        def stop(self):
            pass

    qtcore.Signal = Signal
    qtcore.QThread = QThread
    qtcore.QTimer = QTimer
    qtcore.Qt = types.SimpleNamespace(AlignCenter=0)

    sys.modules['PySide6'] = pyside6
    sys.modules['PySide6.QtWidgets'] = qtwidgets
    sys.modules['PySide6.QtCore'] = qtcore

from kyo_qa_tool_app import MainWindow


class DummyLabel:
    def __init__(self):
        self._text = ""
    def setText(self, text):
        self._text = text
    def text(self):
        return self._text


class DummyTextEdit:
    def __init__(self):
        self.entries = []
    def append(self, text):
        self.entries.append(text)
    def toPlainText(self):
        return "\n".join(self.entries)


def test_update_status_updates_label_and_log():
    dummy = types.SimpleNamespace()
    dummy.feedback_label = DummyLabel()
    dummy.log_text_edit = DummyTextEdit()
    dummy.log_message = MainWindow.log_message.__get__(dummy, type(dummy))

    MainWindow.update_status(dummy, "info", "Test message")

    assert dummy.feedback_label.text() == "Test message"
    assert "Test message" in dummy.log_text_edit.toPlainText()

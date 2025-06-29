from __future__ import annotations

import sys

try:
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QCursor
    from PySide6.QtWidgets import (
        QApplication,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover - minimal stubs
    import types

    Qt = types.SimpleNamespace(ArrowCursor=0)

    class Signal:  # type: ignore
        def __init__(self, *a, **k) -> None:
            pass
        def emit(self, *a, **k) -> None:
            pass
        def connect(self, *a, **k) -> None:
            pass

    class QThread:
        pass

    class QCursor:
        def __init__(self, *a, **k):
            pass

    QApplication = QMainWindow = QWidget = object
    QLabel = QPushButton = QTextEdit = QMessageBox = object
    QVBoxLayout = object

import logging_utils
import processing_engine

# Ensure tests that stub openpyxl don't interfere with later imports
sys.modules.pop("openpyxl", None)

logger = logging_utils.setup_logger("app")


class QtWidgetHandler(logging_utils.logging.Handler):
    """Simple logging handler that writes messages to a Qt widget."""

    def __init__(self, widget: QTextEdit) -> None:
        super().__init__()
        self.widget = widget

    def emit(self, record: logging_utils.logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            if hasattr(self.widget, "append"):
                self.widget.append(msg)
        except Exception:  # pragma: no cover - best effort
            pass


class Worker(QThread):
    """Runs processing tasks in a background thread."""

    update_status = Signal(str)
    update_progress = Signal(int)
    finished = Signal(str)

    def __init__(self, mode: str, path: str, kb_filepath: str) -> None:
        super().__init__()
        self.mode = mode
        self.path = path
        self.kb_filepath = kb_filepath

    def run(self) -> None:  # pragma: no cover - logic tested via signals
        try:
            if self.mode == "folder":
                processing_engine.process_folder(self.path, self.kb_filepath)
            else:
                processing_engine.process_zip_archive(self.path, self.kb_filepath)
            self.finished.emit("Done")
        except Exception as exc:  # pragma: no cover - error path
            logger.exception("Worker error", exc_info=exc)
            message = f"Error: {exc}"
            self.update_status.emit(message)
            self.finished.emit(message)


class MainWindow(QMainWindow):
    """Base Qt window providing logging helpers."""

    def __init__(self) -> None:
        super().__init__()
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        self.feedback_label = QLabel()
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        layout.addWidget(self.feedback_label)
        layout.addWidget(self.log_text_edit)

    def log_message(self, message: str) -> None:
        self.log_text_edit.append(message)
        logger.info(message)

    def update_status(self, level: str, message: str) -> None:
        self.feedback_label.setText(message)
        self.log_message(message)

    def show_error(self, title: str, message: str) -> None:  # pragma: no cover
        QMessageBox.critical(self, title, message)


class KyoQAToolApp(MainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.start_btn = QPushButton("Start")
        self.folder_btn = QPushButton("Folder")
        self.zip_btn = QPushButton("Zip")
        self.excel_btn = QPushButton("Excel")

    def log(self, msg: str) -> None:
        self.log_message(msg)

    def on_done(self, result: str) -> None:
        self.setCursor(QCursor(Qt.ArrowCursor))
        for btn in (self.folder_btn, self.zip_btn, self.excel_btn, self.start_btn):
            btn.setEnabled(True)
        self.log(result)
        if isinstance(result, str) and result.startswith("Error"):
            self.show_error("Processing Error", result)


class QAApp(KyoQAToolApp):
    """Backward compatibility alias for older code/tests."""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = QAApp()
    win.show()
    sys.exit(app.exec())

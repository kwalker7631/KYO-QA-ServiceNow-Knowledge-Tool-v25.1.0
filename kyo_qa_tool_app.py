# KYO QA GUI REFACTOR - IMPROVED NAV + FEEDBACK + ACTIVITY INDICATORS
import sys, os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QTextEdit, QMessageBox, QHBoxLayout, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QCursor

from logging_utils import setup_logger


class MainWindow:
    """Utility wrapper used in tests for status updates."""

    @staticmethod
    def log_message(self, message):
        if hasattr(self, "log_text_edit"):
            self.log_text_edit.append(message)

    @staticmethod
    def update_status(self, tag, message):
        if hasattr(self, "feedback_label"):
            self.feedback_label.setText(message)
        MainWindow.log_message(self, message)

logger = setup_logger("gui")

class Worker(QThread):
    update_progress = Signal(int)
    update_status = Signal(str)
    finished = Signal(str)

    def __init__(self, mode, path, kb_path):
        super().__init__()
        self.mode = mode
        self.path = path
        self.kb_path = kb_path

    def run(self):
        try:
            # Delayed import to avoid circular dependency
            from processing_engine import process_folder, process_zip_archive

            if self.mode == 'folder':
                _, updated, failed = process_folder(self.path, self.kb_path, self.progress_cb, self.status_cb, self.ocr_cb, self.review_cb, self.cancel_flag)
            elif self.mode == 'zip':
                _, updated, failed = process_zip_archive(self.path, self.kb_path, self.progress_cb, self.status_cb, self.ocr_cb, self.review_cb, self.cancel_flag)
            else:
                updated, failed = 0, 0
            self.finished.emit(f"Updated: {updated}, Failed: {failed}")
        except Exception as e:
            logger.exception("Worker thread failed", exc_info=e)
            self.update_status.emit(f"Error: {e}")
            self.finished.emit(f"Error: {e}")

    def progress_cb(self, msg):
        self.update_progress.emit(1)
        self.update_status.emit(msg)

    def status_cb(self, tag, msg):
        self.update_status.emit(f"{tag}: {msg}")

    def ocr_cb(self):
        self.update_status.emit("OCR triggered")

    def review_cb(self):
        self.update_status.emit("Needs manual review")

    def cancel_flag(self):
        return False

class QAApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KYO QA Knowledge Tool")
        self.setGeometry(200, 200, 800, 500)
        self.kb_path = None
        self.selected_folder = None
        self.selected_zip = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        file_group = QGroupBox("Select Files to Process")
        fg_layout = QHBoxLayout()

        self.folder_btn = QPushButton("Select Folder")
        self.folder_btn.clicked.connect(self.select_folder)
        fg_layout.addWidget(self.folder_btn)

        self.zip_btn = QPushButton("Select ZIP File")
        self.zip_btn.clicked.connect(self.select_zip)
        fg_layout.addWidget(self.zip_btn)

        self.excel_btn = QPushButton("Select Excel File")
        self.excel_btn.clicked.connect(self.select_excel)
        fg_layout.addWidget(self.excel_btn)

        file_group.setLayout(fg_layout)
        layout.addWidget(file_group)

        # --- New Start Button
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.start_btn)
        # ---

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        layout.addWidget(QLabel("Process Log:"))
        layout.addWidget(self.status_box)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def update_start_btn_state(self):
        ready = bool(self.kb_path and (self.selected_folder or self.selected_zip))
        self.start_btn.setEnabled(ready)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose Folder")
        if path:
            self.selected_folder = path
            self.selected_zip = None
            self.log(f"Selected folder: {path}")
            self.update_start_btn_state()
        elif not self.kb_path:
            self.show_error("No Excel File", "Please select an Excel file first.")

    def select_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose ZIP", filter="Zip files (*.zip)")
        if path:
            self.selected_zip = path
            self.selected_folder = None
            self.log(f"Selected ZIP: {path}")
            self.update_start_btn_state()
        elif not self.kb_path:
            self.show_error("No Excel File", "Please select an Excel file first.")

    def select_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Excel File", filter="Excel (*.xlsx *.xls)")
        if path:
            self.kb_path = path
            self.log(f"Selected Excel: {path}")
            self.show_headers(path)
            self.update_start_btn_state()

    def show_headers(self, xlsx_path):
        try:
            import pandas as pd
            df = pd.read_excel(xlsx_path, engine="openpyxl")
            headers = list(df.columns)
            self.log(f"Headers Found: {headers}")
        except Exception as e:
            self.show_error("Header Read Error", f"Failed to read headers: {e}")

    def log(self, message):
        self.status_box.append(message)
        logger.info(message)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)
        logger.error(f"{title}: {message}")

    def start_processing(self):
        if self.selected_folder:
            self.start_worker('folder', self.selected_folder)
        elif self.selected_zip:
            self.start_worker('zip', self.selected_zip)

    def start_worker(self, mode, path):
        self.setCursor(QCursor(Qt.WaitCursor))
        self.folder_btn.setEnabled(False)
        self.zip_btn.setEnabled(False)
        self.excel_btn.setEnabled(False)
        self.start_btn.setEnabled(False)

        self.worker = Worker(mode, path, self.kb_path)
        self.worker.update_progress.connect(self.increment_progress)
        self.worker.update_status.connect(self.log)
        self.worker.finished.connect(self.on_done)
        self.progress.setValue(0)
        self.worker.start()

    def increment_progress(self, value):
        self.progress.setValue(self.progress.value() + value)

    def on_done(self, message):
        self.setCursor(QCursor(Qt.ArrowCursor))
        if str(message).startswith("Error:"):
            # Keep controls disabled until the user closes the error dialog
            self.log(message)
            self.show_error("Processing Error", str(message))
            self.folder_btn.setEnabled(True)
            self.zip_btn.setEnabled(True)
            self.excel_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
        else:
            self.folder_btn.setEnabled(True)
            self.zip_btn.setEnabled(True)
            self.excel_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.log(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = QAApp()
    win.show()
    sys.exit(app.exec())
class QAApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KYO QA Knowledge Tool")
        self.setGeometry(200, 200, 800, 500)
        self.kb_path = None
        self.selected_folder = None
        self.selected_zip = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        file_group = QGroupBox("Select Files to Process")
        fg_layout = QHBoxLayout()

        self.folder_btn = QPushButton("Select Folder")
        self.folder_btn.clicked.connect(self.select_folder)
        fg_layout.addWidget(self.folder_btn)

        self.zip_btn = QPushButton("Select ZIP File")
        self.zip_btn.clicked.connect(self.select_zip)
        fg_layout.addWidget(self.zip_btn)

        self.excel_btn = QPushButton("Select Excel File")
        self.excel_btn.clicked.connect(self.select_excel)
        fg_layout.addWidget(self.excel_btn)

        file_group.setLayout(fg_layout)
        layout.addWidget(file_group)

        # --- New Start Button
        self.start_btn = QPushButton("Start Processing")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_processing)
        layout.addWidget(self.start_btn)
        # ---

        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        layout.addWidget(QLabel("Process Log:"))
        layout.addWidget(self.status_box)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def update_start_btn_state(self):
        ready = bool(self.kb_path and (self.selected_folder or self.selected_zip))
        self.start_btn.setEnabled(ready)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose Folder")
        if path:
            self.selected_folder = path
            self.selected_zip = None
            self.log(f"Selected folder: {path}")
            self.update_start_btn_state()
        elif not self.kb_path:
            self.show_error("No Excel File", "Please select an Excel file first.")

    def select_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose ZIP", filter="Zip files (*.zip)")
        if path:
            self.selected_zip = path
            self.selected_folder = None
            self.log(f"Selected ZIP: {path}")
            self.update_start_btn_state()
        elif not self.kb_path:
            self.show_error("No Excel File", "Please select an Excel file first.")

    def select_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Excel File", filter="Excel (*.xlsx *.xls)")
        if path:
            self.kb_path = path
            self.log(f"Selected Excel: {path}")
            self.show_headers(path)
            self.update_start_btn_state()

    def show_headers(self, xlsx_path):
        try:
            import pandas as pd
            df = pd.read_excel(xlsx_path, engine="openpyxl")
            headers = list(df.columns)
            self.log(f"Headers Found: {headers}")
        except Exception as e:
            self.show_error("Header Read Error", f"Failed to read headers: {e}")

    def log(self, message):
        self.status_box.append(message)
        logger.info(message)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)
        logger.error(f"{title}: {message}")

    def start_processing(self):
        if self.selected_folder:
            self.start_worker('folder', self.selected_folder)
        elif self.selected_zip:
            self.start_worker('zip', self.selected_zip)

    def start_worker(self, mode, path):
        self.setCursor(QCursor(Qt.WaitCursor))
        self.folder_btn.setEnabled(False)
        self.zip_btn.setEnabled(False)
        self.excel_btn.setEnabled(False)
        self.start_btn.setEnabled(False)

        self.worker = Worker(mode, path, self.kb_path)
        self.worker.update_progress.connect(self.increment_progress)
        self.worker.update_status.connect(self.log)
        self.worker.finished.connect(self.on_done)
        self.progress.setValue(0)
        self.worker.start()

    def increment_progress(self, value):
        self.progress.setValue(self.progress.value() + value)

    def on_done(self, message):
        self.setCursor(QCursor(Qt.ArrowCursor))
        if str(message).startswith("Error:"):
            self.log(message)
            self.show_error("Processing Error", str(message))
            self.folder_btn.setEnabled(True)
            self.zip_btn.setEnabled(True)
            self.excel_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
        else:
            self.folder_btn.setEnabled(True)
            self.zip_btn.setEnabled(True)
            self.excel_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.log(message)
main

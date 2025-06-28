# KYO QA GUI REFACTOR - IMPROVED NAV + FEEDBACK
import sys, os
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QProgressBar, QTextEdit, QMessageBox, QHBoxLayout, QGroupBox
)
from PySide6.QtCore import Qt

from processing_engine import process_folder, process_zip_archive
from logging_utils import setup_logger

logger = setup_logger("gui")

class QAApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KYO QA Knowledge Tool")
        self.setGeometry(200, 200, 800, 500)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        layout = QVBoxLayout()

        # File Selection Buttons
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

        # Status Box
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        layout.addWidget(QLabel("Process Log:"))
        layout.addWidget(self.status_box)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Choose Folder")
        if path:
            self.log(f"Selected folder: {path}")
            # Here you would call: process_folder(path, ...)

    def select_zip(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose ZIP", filter="Zip files (*.zip)")
        if path:
            self.log(f"Selected ZIP: {path}")
            # Here you would call: process_zip_archive(path, ...)

    def select_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose Excel File", filter="Excel (*.xlsx *.xls)")
        if path:
            self.log(f"Selected Excel: {path}")
            self.show_headers(path)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = QAApp()
    win.show()
    sys.exit(app.exec())

# KYO QA ServiceNow Tool - FINAL All-in-One Version (Corrected)
# This script contains the launcher, UI definition, and all necessary methods.

import sys
import os
import re
import time
import threading
from pathlib import Path

# --- PySide6 Imports ---
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QStatusBar, QGroupBox, QLineEdit, QPushButton, QFileDialog, QProgressBar, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

# --- Project Module Imports ---
try:
    from version import VERSION
    from gui_components import RudeButton, StatusIndicator
    from processing_engine import process_folder, process_zip_archive
    from file_utils import ensure_folders, cleanup_temp_files, open_file
    from logging_utils import setup_logger
except ImportError as e:
    print(f"FATAL ERROR: A required .py file is missing or corrupted: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

logger = setup_logger("app_ui")

# --- Final Stylesheet ---
STYLESHEET = """
    QMainWindow { background-color: #FFFFFF; font-family: "Segoe UI"; }
    #header { background-color: #231F20; border-bottom: 4px solid #E31A2F; }
    #logoLabel { color: #E31A2F; font-family: "Arial Black"; font-size: 26px; padding: 5px 0 5px 15px; }
    #titleLabel { color: #FFFFFF; font-size: 18px; font-weight: bold; padding-top: 8px; }
    QGroupBox { font-size: 11pt; font-weight: bold; color: #231F20; border: 1px solid #D0D0D0; border-radius: 8px; margin-top: 1ex; background-color: #F5F5F5; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 10px; background-color: #F5F5F5; border-radius: 4px;}
    QPushButton { background-color: #0A9BCD; color: white; font-weight: bold; font-size: 10pt; padding: 10px 15px; border-radius: 5px; border: none; }
    QPushButton:hover { background-color: #0dbdeF; }
    #startButton { background-color: #E31A2F; font-size: 13px; }
    #startButton:hover { background-color: #ff4c61; }
    QProgressBar { border: 1px solid #BFBFBF; border-radius: 5px; text-align: center; font-weight: bold; color: #FFFFFF; }
    QProgressBar::chunk { background-color: #0A9BCD; border-radius: 4px; }
    #feedbackLabel { font-size: 10pt; font-style: italic; color: #333333; }
"""

class ProcessingWorker(QThread):
    progress_updated = Signal(str)
    status_updated = Signal(str, str)
    processing_finished = Signal(str, int, int)
    processing_error = Signal(str, str)
    file_succeeded = Signal()
    file_failed = Signal()
    ocr_used_signal = Signal()
    needs_review_signal = Signal()

    def __init__(self, process_path, kb_path, parent=None):
        super().__init__(parent)
        self.process_path = process_path
        self.kb_path = kb_path
        self.cancel_event = threading.Event()

    def run(self):
        try:
            path_obj = Path(self.process_path)
            process_func = process_folder if path_obj.is_dir() else process_zip_archive
            updated_path, updated, failed = process_func(self.process_path, self.kb_path, self.progress_updated.emit, self.status_updated.emit, lambda: None, self.cancel_event)
            self.processing_finished.emit(updated_path, updated, failed)
        except Exception as e:
            logger.error("Error in worker thread", exc_info=True)
            self.processing_error.emit("Processing Failed", str(e))

    def stop(self):
        self.cancel_event.set()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.result_file_path = None
        self._setup_window_and_widgets()
        self.setStyleSheet(STYLESHEET)
        # Register GUI log handler now that the text edit widget exists
        setup_logger("app_ui", log_widget=self.log_text_edit)

    def _setup_window_and_widgets(self):
        self.setWindowTitle(f"Kyocera QA ServiceNow Knowledge Tool v{VERSION}")
        self.setMinimumSize(950, 700)
        self.resize(1100, 800)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self._create_header()
        central_area = QWidget()
        central_area_layout = QVBoxLayout(central_area)
        central_area_layout.setContentsMargins(15, 15, 15, 15)
        central_area_layout.setSpacing(15)
        self._create_io_section(central_area_layout)
        self._create_controls_section(central_area_layout)
        self._create_feedback_section(central_area_layout)
        self._create_log_section(central_area_layout)
        self.main_layout.addWidget(central_area, 1)
        self._create_status_bar()

    def _create_header(self):
        header_widget = QWidget(); header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        logo = QLabel("KYOCERA"); logo.setObjectName("logoLabel")
        title = QLabel("QA ServiceNow Knowledge Tool"); title.setObjectName("titleLabel")
        header_layout.addWidget(logo); header_layout.addWidget(title); header_layout.addStretch()
        self.main_layout.addWidget(header_widget)

    def _create_io_section(self, parent_layout):
        io_groupbox = QGroupBox("1. Select Files"); layout = QGridLayout(io_groupbox)
        self.kb_path_edit = QLineEdit(); self.kb_path_edit.setPlaceholderText("Select your existing .xlsx KB file")
        kb_browse_btn = QPushButton("Browse..."); kb_browse_btn.clicked.connect(self.browse_kb_file)
        self.process_path_edit = QLineEdit(); self.process_path_edit.setPlaceholderText("Select a folder or .zip file of PDFs")
        folder_browse_btn = QPushButton("Select Folder..."); folder_browse_btn.clicked.connect(self.browse_folder)
        zip_browse_btn = QPushButton("Select ZIP..."); zip_browse_btn.clicked.connect(self.browse_zip)
        btn_layout = QHBoxLayout(); btn_layout.addWidget(folder_browse_btn); btn_layout.addWidget(zip_browse_btn); btn_layout.addStretch()
        layout.addWidget(QLabel("Knowledge Base File:"), 0, 0); layout.addWidget(self.kb_path_edit, 0, 1); layout.addWidget(kb_browse_btn, 0, 2)
        layout.addWidget(QLabel("Process Folder/ZIP:"), 1, 0); layout.addWidget(self.process_path_edit, 1, 1); layout.addLayout(btn_layout, 1, 2)
        layout.setColumnStretch(1, 1); parent_layout.addWidget(io_groupbox)

    def _create_controls_section(self, parent_layout):
        controls_groupbox = QGroupBox("2. Process"); layout = QHBoxLayout(controls_groupbox)
        self.start_button = QPushButton("▶ UPDATE KNOWLEDGE BASE"); self.start_button.setObjectName("startButton"); self.start_button.setToolTip("Begin processing...")
        self.open_kb_button = QPushButton("📂 Open KB File"); self.open_kb_button.setToolTip("Open the selected Knowledge Base file.")
        self.clear_inputs_button = QPushButton("✨ Clear Inputs"); self.clear_inputs_button.setToolTip("Clear all file selections.")
        self.rude_button = RudeButton("Rage Click", controls_groupbox); self.rude_button.setVisible(False)
        layout.addWidget(self.start_button, 2); layout.addWidget(self.open_kb_button, 1); layout.addWidget(self.clear_inputs_button, 1); layout.addWidget(self.rude_button, 1)
        parent_layout.addWidget(controls_groupbox)
        self.start_button.clicked.connect(self.start_processing)
        self.open_kb_button.clicked.connect(self.open_kb_file)
        self.clear_inputs_button.clicked.connect(self.clear_inputs)

    def _create_feedback_section(self, parent_layout):
        feedback_groupbox = QGroupBox("3. Live Dashboard"); layout = QVBoxLayout(feedback_groupbox)
        icon_layout = QHBoxLayout(); self.pass_indicator = StatusIndicator("Succeeded", "✅", "#00B176"); self.fail_indicator = StatusIndicator("Failed", "❌", "#E31A2F")
        self.review_indicator = StatusIndicator("Needs Review", "⚠️", "#F5B400"); self.ocr_indicator = StatusIndicator("OCR Used", "👁️", "#0A9BCD")
        icon_layout.addWidget(self.pass_indicator); icon_layout.addWidget(self.fail_indicator); icon_layout.addWidget(self.review_indicator); icon_layout.addWidget(self.ocr_indicator)
        layout.addLayout(icon_layout)
        self.feedback_label = QLabel("Ready to begin processing..."); self.feedback_label.setObjectName("feedbackLabel"); self.feedback_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.feedback_label)
        self.progress_bar = QProgressBar(); layout.addWidget(self.progress_bar); parent_layout.addWidget(feedback_groupbox)

    def _create_log_section(self, parent_layout):
        log_groupbox = QGroupBox("4. Activity Log"); layout = QVBoxLayout(log_groupbox)
        self.log_text_edit = QTextEdit(); self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet("background-color: #FCFCFC; font-family: Consolas; font-size: 9pt;")
        layout.addWidget(self.log_text_edit, 1); parent_layout.addWidget(log_groupbox, 1)

    def _create_status_bar(self):
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar);
        self.status_label = QLabel("Ready."); self.status_bar.addWidget(self.status_label)
        exit_button = QPushButton("Exit"); exit_button.setToolTip("Close the application"); exit_button.setStyleSheet("padding: 4px 15px; background-color: #6c757d;")
        exit_button.clicked.connect(self.close); self.status_bar.addPermanentWidget(exit_button)

    def start_processing(self):
        kb_path, process_path = self.kb_path_edit.text(), self.process_path_edit.text()
        if not kb_path or not process_path: return QMessageBox.warning(self, "Input Missing", "Please select both a KB file and a folder/ZIP.")
        self.update_ui_for_processing(True)
        self.worker = ProcessingWorker(process_path, kb_path)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.status_updated.connect(self.update_status)
        self.worker.file_succeeded.connect(self.pass_indicator.increment)
        self.worker.file_failed.connect(self.fail_indicator.increment)
        self.worker.needs_review_signal.connect(self.review_indicator.increment)
        self.worker.ocr_used_signal.connect(self.ocr_indicator.increment)
        self.worker.processing_finished.connect(self.processing_finished)
        self.worker.processing_error.connect(self.handle_error)
        self.worker.finished.connect(lambda: self.update_ui_for_processing(False))
        self.worker.start()

    def update_ui_for_processing(self, is_processing):
        self.start_button.setEnabled(not is_processing); self.clear_inputs_button.setEnabled(not is_processing)
        self.feedback_label.setText("Processing..." if is_processing else "Processing complete.")
        if not is_processing: self.progress_bar.setValue(0); self.status_label.setText("Ready.")
        else:
            self.status_label.setText("Processing...")
            self.pass_indicator.reset(); self.fail_indicator.reset(); self.review_indicator.reset(); self.ocr_indicator.reset()
            self.rude_button.setVisible(False); self.log_text_edit.clear()

    def update_progress(self, message):
        self.log_message(message)
        match = re.search(r"Processing (\d+)/(\d+)", message)
        if match: self.progress_bar.setValue(int((int(match.group(1)) / int(match.group(2))) * 100))

    def update_status(self, category, message):
        self.feedback_label.setText(message)

    def handle_error(self, title, message):
        logger.error(f"{title}: {message}", exc_info=True); self.log_message(f"ERROR: {message}")
        QMessageBox.critical(self, title, message); self.rude_button.setVisible(True); self.rude_button.start_animation()

    def processing_finished(self, updated_path, updated_count, failed_count):
        self.result_file_path = updated_path
        self.log_message(f"Finished! {updated_count} records updated, {failed_count} files failed.")
        if QMessageBox.question(self, "Processing Complete", f"Success!\n- Records Updated: {updated_count}\n- Files Failed: {failed_count}\n\nWould you like to open the updated file?") == QMessageBox.Yes: self.open_kb_file()

    # --- FIX: Restoring all missing helper methods ---
    def log_message(self, text):
        timestamp = time.strftime("%H:%M:%S"); self.log_text_edit.append(f"[{timestamp}] {text}")
    def browse_kb_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select KB File", "", "Excel Files (*.xlsx)");
        if filepath: self.kb_path_edit.setText(filepath)
    def browse_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Folder of PDFs");
        if dir_path: self.process_path_edit.setText(dir_path)
    def browse_zip(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select ZIP Archive", "", "ZIP Files (*.zip)");
        if filepath: self.process_path_edit.setText(filepath)
    def clear_inputs(self):
        self.kb_path_edit.clear(); self.process_path_edit.clear(); self.log_message("Inputs cleared.")
    def open_kb_file(self):
        kb_path = self.kb_path_edit.text()
        if kb_path and Path(kb_path).exists(): open_file(kb_path)
        else: QMessageBox.warning(self, "File Not Found", "Please select a valid Knowledge Base file first.")
    def on_closing(self):
        if self.worker and self.worker.isRunning():
            if QMessageBox.question(self, "Exit Confirmation", "Processing is in progress. Are you sure?") == QMessageBox.Yes: self.worker.stop(); self.close()
        else: self.close()

def main():
    """Launches the application."""
    ensure_folders()
    cleanup_temp_files()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
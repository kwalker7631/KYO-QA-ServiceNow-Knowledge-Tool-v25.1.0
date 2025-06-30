# kyo_qa_tool_app.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import queue
import time
import importlib

from config import BRAND_COLORS
from processing_engine import run_processing_job
from file_utils import open_file, ensure_folders, cleanup_temp_files
from kyo_review_tool import ReviewWindow
from version import VERSION
import logging_utils
from gui_components import (
    create_main_header, create_io_section, 
    create_process_controls, create_status_and_log_section
)

logger = logging_utils.setup_logger("app")

class KyoQAToolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # --- App State & UI Vars ---
        self.is_processing = False
        self.is_paused = False
        self.result_file_path = None
        self.reviewable_files = []
        self.start_time = None
        self.last_run_info = {}
        self.response_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self.selected_folder = tk.StringVar()
        self.selected_excel = tk.StringVar()
        self.selected_files_list = []
        self.status_current_file = tk.StringVar(value="Idle")
        self.progress_value = tk.DoubleVar(value=0)
        self.time_remaining_var = tk.StringVar(value="")
        self.count_pass, self.count_fail, self.count_review, self.count_ocr = (tk.IntVar(value=0) for _ in range(4))
        self.led_status_var = tk.StringVar(value="[Idle]")

        self.style = ttk.Style(self)
        self._setup_window_styles()
        self._create_widgets()
        ensure_folders()
        self.after(100, self.process_response_queue)
    
    def _setup_window_styles(self):
        self.title(f"Kyocera QA Knowledge Tool v{VERSION}")
        self.geometry("1100x900")
        self.minsize(950, 800)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.configure(bg=BRAND_COLORS["background"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.style.theme_use("clam")
        # ... all style configurations
    
    def _create_widgets(self):
        create_main_header(self, VERSION, BRAND_COLORS)
        main_frame = ttk.Frame(self, padding=15)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        create_io_section(main_frame, self)
        create_process_controls(main_frame, self)
        create_status_and_log_section(main_frame, self)
    
    def start_processing(self, job=None, is_rerun=False):
        if self.is_processing: return
        
        if not job:
            input_path = self.selected_folder.get() or self.selected_files_list
            if not input_path: messagebox.showwarning("Input Missing", "Please select files or a folder."); return
            excel_path = self.selected_excel.get()
            if not excel_path: messagebox.showwarning("Input Missing", "Please select a base Excel file."); return
            job = {"excel_path": excel_path, "input_path": input_path}
            self.last_run_info = job
        
        job["is_rerun"], job["pause_event"] = is_rerun, self.pause_event
        self.update_ui_for_start(); self.log_message("Starting job...")
        self.start_time = time.time()
        threading.Thread(target=run_processing_job, args=(job, self.response_queue, self.cancel_event, self.pause_event), daemon=True).start()
        
    def rerun_flagged_job(self):
        if not self.reviewable_files: messagebox.showwarning("No Files", "No files to re-run."); return
        if not self.result_file_path: messagebox.showerror("Error", "Previous result file not found."); return
        files = [item['pdf_path'] for item in self.reviewable_files]
        self.log_message(f"Re-running on {len(files)} flagged files...")
        self.start_processing(job={"excel_path": self.result_file_path, "input_path": files}, is_rerun=True)

    # ... and all other methods
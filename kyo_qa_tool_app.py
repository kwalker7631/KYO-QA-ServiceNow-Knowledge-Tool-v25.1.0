import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import queue
import time
import os

# Local module imports
from config import BRAND_COLORS, ASSETS_DIR, get_app_version, OUTPUT_DIR
from processing_engine import run_processing_job
from file_utils import open_file
from kyo_review_tool import ReviewWindow
import logging_utils
from gui_components import (
    create_main_header, create_io_section,
    create_process_controls, create_status_and_log_section,
    create_review_section, ToolTip
)

logger = logging_utils.setup_logger("app")
VERSION = get_app_version()

class KyoQAToolApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- Variable Declarations ---
        self.is_processing = False
        self.is_paused = False
        self.result_file_path = None
        self.review_files = tk.StringVar(value=[])
        self.start_time = None
        self.last_run_info = {}
        self.response_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self.selected_folder = tk.StringVar()
        self.selected_excel = tk.StringVar()
        self.selected_files_list = []
        self.status_current_file = tk.StringVar(value="Ready to process")
        self.progress_value = tk.DoubleVar(value=0)
        self.time_remaining_var = tk.StringVar(value="Time Remaining: N/A")
        self.pass_count = tk.IntVar(value=0)
        self.fail_count = tk.IntVar(value=0)
        self.review_count = tk.IntVar(value=0)
        self.ocr_count = tk.IntVar(value=0)

        # --- UI Setup ---
        self.style = ttk.Style(self)
        self._setup_window_styles()
        self._create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(100, self.process_response_queue)
        self.update_review_list()
        logger.info(f"Kyo QA Tool v{VERSION} initialized successfully.")

    def _setup_window_styles(self):
        self.title(f"Kyocera QA Knowledge Tool v{VERSION}")
        self.geometry("1200x850")
        self.minsize(1100, 750)
        # --- FIX: Corrected the unterminated string literal ---
        self.configure(bg=BRAND_COLORS["background"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1) # Allow the review section to expand
        self.style.theme_use("clam")
        self.style.configure("Header.TFrame", background=BRAND_COLORS["header"])
        self.style.configure("Header.TLabel", background=BRAND_COLORS["header"], foreground="white", font=("Segoe UI", 12, "bold"))
        self.style.configure("Header.TButton", background=BRAND_COLORS["header"], foreground="white", font=("Segoe UI", 9, "bold"))
        self.style.map("Header.TButton", background=[("active", BRAND_COLORS["purple"])])
        self.style.configure("Accent.TButton", foreground="white", background=BRAND_COLORS["purple"], font=("Segoe UI", 10, "bold"))
        self.style.map("Accent.TButton", background=[("active", "#8A4DB3")])

    def _create_widgets(self):
        create_main_header(self, VERSION, BRAND_COLORS)
        # Pass `self` as the parent for the main sections
        create_io_section(self, self)
        create_process_controls(self, self)
        create_status_and_log_section(self, self)
        create_review_section(self, self)

    def start_processing(self, is_rerun=False):
        if self.is_processing: return
        
        input_path = self.selected_files_list or self.selected_folder.get()
        if not input_path and not is_rerun:
            messagebox.showwarning("Input Missing", "Please select a folder or files to process.")
            return
            
        excel_path = self.selected_excel.get()
        if not excel_path:
            messagebox.showwarning("Input Missing", "Please select a base Excel file.")
            return
            
        job = {
            "excel_path": excel_path,
            "input_path": input_path,
            "output_dir": Path(excel_path).parent,
            "is_rerun": is_rerun
        }
        
        self.update_ui_for_start()
        log_target = "flagged files" if is_rerun else (Path(self.selected_folder.get()).name if self.selected_folder.get() else f"{len(self.selected_files_list)} files")
        self.log_message(f"Starting job for: {log_target}", "info")
        
        threading.Thread(target=run_processing_job, args=(job, self.response_queue, self.cancel_event, self.pause_event), daemon=True).start()

    def browse_excel(self):
        path = filedialog.askopenfilename(title="Select Excel Template", filetypes=[("Excel Files", "*.xlsx *.xlsm")])
        if path: self.selected_excel.set(path)

    def browse_folder(self):
        path = filedialog.askdirectory(title="Select Folder with PDFs")
        if path:
            self.selected_folder.set(path)
            self.selected_files_list = []

    def browse_files(self):
        paths = filedialog.askopenfilenames(title="Select PDF Files", filetypes=[("PDF Files", "*.pdf")])
        if paths:
            self.selected_files_list = list(paths)
            self.selected_folder.set("")

    def on_closing(self):
        if self.is_processing and not messagebox.askyesno("Exit", "Processing is running. Are you sure?"):
            return
        self.cancel_event.set()
        self.destroy()

    def process_response_queue(self):
        try:
            while not self.response_queue.empty():
                msg = self.response_queue.get_nowait()
                msg_type = msg.get("type")

                if msg_type == "finish":
                    self.update_ui_for_finish(msg.get("status", "Complete"))
                elif msg_type == "status":
                    self.status_current_file.set(msg.get("msg"))
                elif msg_type == "progress":
                    self.progress_value.set(msg.get("value"))
                elif msg_type == "result_path":
                    self.result_file_path = msg.get("path")
                    self.open_result_btn.config(state=tk.NORMAL)
                elif msg_type == "update_counts":
                    self.pass_count.set(msg.get("pass", 0))
                    self.fail_count.set(msg.get("fail", 0))
                    self.review_count.set(msg.get("review", 0))
                    self.ocr_count.set(msg.get("ocr", 0))

        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_response_queue)

    def update_ui_for_start(self):
        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.rerun_btn.config(state=tk.DISABLED)
        self.open_result_btn.config(state=tk.DISABLED)
        self.pass_count.set(0)
        self.fail_count.set(0)
        self.review_count.set(0)
        self.ocr_count.set(0)

    def update_ui_for_finish(self, status):
        self.is_processing = False
        self.status_current_file.set(f"Job {status}!")
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="Pause")
        self.stop_btn.config(state=tk.DISABLED)
        self.rerun_btn.config(state=tk.NORMAL)
        self.is_paused = False
        self.pause_event.clear()
        self.update_review_list()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_event.set()
            self.pause_btn.config(text="Resume")
        else:
            self.pause_event.clear()
            self.pause_btn.config(text="Pause")

    def stop_processing(self):
        if messagebox.askyesno("Stop Job", "Are you sure you want to stop the current job?"):
            self.cancel_event.set()

    def open_review_tool(self):
        ReviewWindow(self, "MODEL_PATTERNS", "Model Search Patterns")

    def open_result_file(self):
        if self.result_file_path and Path(self.result_file_path).exists():
            open_file(self.result_file_path)
        else:
            messagebox.showerror("Error", "Result file not found or has been moved.")

    def update_review_list(self):
        review_dir = OUTPUT_DIR / "needs_review"
        if review_dir.exists():
            files = [f.name for f in review_dir.iterdir() if f.suffix == '.txt']
            self.review_files.set(files)
        else:
            self.review_files.set([])

    def review_selected_file(self):
        selected_indices = self.review_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Info", "Please select a file from the list to review.")
            return
        
        filename = self.review_listbox.get(selected_indices[0])
        file_path = OUTPUT_DIR / "needs_review" / filename
        
        file_info = {"txt_path": file_path}
        ReviewWindow(self, "MODEL_PATTERNS", "Model Search Patterns", file_info)

    def toggle_fullscreen(self, event=None):
        is_fullscreen = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_fullscreen)

if __name__ == "__main__":
    app = KyoQAToolApp()
    app.mainloop()

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
        
        # Initialize counters FIRST (before any widgets)
        self.count_pass = tk.IntVar(value=0)
        self.count_fail = tk.IntVar(value=0)
        self.count_review = tk.IntVar(value=0)
        self.count_ocr = tk.IntVar(value=0)
        
        # Initialize all other variables
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
        self.led_status_var = tk.StringVar(value="[Idle]")

        # Now set up styles and create widgets
        self.style = ttk.Style(self)
        self._setup_window_styles()
        self._create_widgets()
        
        # Ensure folders exist
        ensure_folders()
        
        # Start the response queue processor
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
        
        # Configure all styles
        self.style.configure("TFrame", background=BRAND_COLORS["background"])
        self.style.configure("Header.TFrame", background=BRAND_COLORS["background"])
        self.style.configure("Dark.TFrame", background=BRAND_COLORS["frame_background"])
        
        self.style.configure("TLabel", background=BRAND_COLORS["background"])
        self.style.configure("Status.TLabel", background=BRAND_COLORS["frame_background"], font=("Segoe UI", 9))
        self.style.configure("Status.Header.TLabel", background=BRAND_COLORS["frame_background"], font=("Segoe UI", 9, "bold"))
        self.style.configure("Status.Count.TLabel", background=BRAND_COLORS["frame_background"], font=("Segoe UI", 10, "bold"))
        self.style.configure("LED.TLabel", background=BRAND_COLORS["frame_background"], font=("Consolas", 10, "bold"))
        
        self.style.configure("TLabelFrame", background=BRAND_COLORS["background"], relief="groove", borderwidth=2)
        self.style.configure("TLabelFrame.Label", background=BRAND_COLORS["background"], font=("Segoe UI", 10, "bold"))
        
        self.style.configure("TButton", font=("Segoe UI", 9))
        self.style.map("TButton",
            background=[('active', '#D0D0D0'), ('!active', '#F0F0F0')],
            foreground=[('active', 'black'), ('!active', 'black')]
        )
        
        self.style.configure("Red.TButton", font=("Segoe UI", 11, "bold"))
        self.style.map("Red.TButton",
            background=[('active', '#CC0025'), ('!active', BRAND_COLORS["kyocera_red"])],
            foreground=[('active', 'white'), ('!active', 'white')]
        )
        
        self.style.configure("TEntry", fieldbackground="white", borderwidth=1, relief="solid")
        self.style.configure("TProgressbar", background=BRAND_COLORS["accent_blue"])
        self.style.configure("Blue.Horizontal.TProgressbar", background=BRAND_COLORS["accent_blue"])
        
        # Additional styles
        self.style.configure("TSeparator", background="#E0E0E0")
    
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
        if not self.reviewable_files:
            messagebox.showwarning("No Files", "No files to re-run.")
            return
        if not self.result_file_path:
            messagebox.showerror("Error", "Previous result file not found.")
            return

        files = [item["pdf_path"] for item in self.reviewable_files]
        self.log_message(f"Re-running on {len(files)} flagged files...")
        self.start_processing(job={"excel_path": self.result_file_path, "input_path": files}, is_rerun=True)

    def browse_excel(self):
        path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xlsm")],
        )
        if path:
            self.selected_excel.set(path)
            self.log_message(f"Excel selected: {path}")

    def browse_folder(self):
        path = filedialog.askdirectory(title="Select Folder")
        if path:
            self.selected_folder.set(path)
            self.selected_files_list = []
            if hasattr(self, "files_label"):
                self.files_label.config(text="0 files selected")
            self.log_message(f"Folder selected: {path}")

    def browse_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if paths:
            self.selected_files_list = list(paths)
            self.selected_folder.set("")
            if hasattr(self, "files_label"):
                self.files_label.config(text=f"{len(paths)} files selected")
            self.log_message(f"{len(paths)} files selected")

    def toggle_pause(self):
        if not self.is_processing:
            return
        if self.is_paused:
            self.is_paused = False
            self.pause_event.clear()
            self.pause_btn.config(text="⏯️ Pause")
            self.log_message("Resuming...")
        else:
            self.is_paused = True
            self.pause_event.set()
            self.pause_btn.config(text="▶ Resume")
            self.log_message("Paused.")

    def stop_processing(self):
        if not self.is_processing:
            return
        self.cancel_event.set()
        self.log_message("Stopping after current file...")

    def on_closing(self):
        if self.is_processing:
            if not messagebox.askyesno(
                "Exit", "Processing is running. Quit anyway?"
            ):
                return
            self.cancel_event.set()

        cleanup_temp_files()
        self.destroy()

    def open_result(self):
        if self.result_file_path:
            open_file(self.result_file_path)

    def open_pattern_manager(self):
        file_info = self.reviewable_files[0] if self.reviewable_files else None
        ReviewWindow(self, "MODEL_PATTERNS", "Model Patterns", file_info)

    def log_message(self, message, tag="info"):
        getattr(logger, tag, logger.info)(message)
        if hasattr(self, "log_text"):
            try:
                self.log_text.insert(tk.END, message + "\n", tag)
                self.log_text.see(tk.END)
            except tk.TclError:
                pass

    def update_ui_for_start(self):
        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.review_btn.config(state=tk.DISABLED)
        self.open_result_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.DISABLED)

    def update_ui_for_finish(self):
        self.is_processing = False
        self.is_paused = False
        self.pause_event.clear()
        self.process_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="⏯️ Pause")
        self.stop_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.NORMAL)
        self.review_btn.config(state=tk.NORMAL)
        if self.result_file_path:
            self.open_result_btn.config(state=tk.NORMAL)
        if self.reviewable_files:
            self.rerun_btn.config(state=tk.NORMAL)

    def handle_finished_job(self, status):
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.log_message(f"Job finished: {status} in {elapsed:.1f}s", "info")
        self.update_ui_for_finish()

    def update_review_listbox(self):
        """Update the review listbox with current reviewable files."""
        if hasattr(self, 'review_listbox'):
            self.review_listbox.delete(0, tk.END)
            for item in self.reviewable_files:
                display_text = f"{item.get('filename', 'Unknown')} - {item.get('reason', 'Review needed')}"
                self.review_listbox.insert(tk.END, display_text)

    def process_response_queue(self):
        while not self.response_queue.empty():
            msg = self.response_queue.get()
            mtype = msg.get("type")
            if mtype == "log":
                self.log_message(msg.get("msg", ""), msg.get("tag", "info"))
            elif mtype == "status":
                self.status_current_file.set(msg.get("msg", ""))
                self.led_status_var.set(f"[{msg.get('led','')}]")
            elif mtype == "progress":
                cur = msg.get("current", 0)
                total = msg.get("total", 1)
                self.progress_value.set((cur / total) * 100)
            elif mtype == "increment_counter":
                var = getattr(self, f"count_{msg.get('counter')}", None)
                if isinstance(var, tk.IntVar):
                    var.set(var.get() + 1)
            elif mtype == "review_item":
                self.reviewable_files.append(msg.get("data"))
                self.count_review.set(self.count_review.get() + 1)
                self.update_review_listbox()  # Add this line
            elif mtype == "result_path":
                self.result_file_path = msg.get("path")
            elif mtype == "finish":
                self.handle_finished_job(msg.get("status", "Complete"))

        self.after(100, self.process_response_queue)


if __name__ == "__main__":
    try:
        app = KyoQAToolApp()
        app.mainloop()
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
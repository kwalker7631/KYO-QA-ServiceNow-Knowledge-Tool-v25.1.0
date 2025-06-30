# kyo_qa_tool_app.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import queue
import time
import sys

from config import BRAND_COLORS
from file_utils import open_file, ensure_folders, cleanup_temp_files
from kyo_review_tool import ReviewWindow
from version import VERSION
import logging_utils
import processing_engine
import sys

# Ensure tests that stub openpyxl don't interfere with later imports
sys.modules.pop("openpyxl", None)


def gui_callback(func):
    """Decorator to log unexpected GUI errors and show a simple dialog."""

    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as exc:  # pragma: no cover - defensive
            logging_utils.log_exception(logger, f"GUI error in {func.__name__}")
            messagebox.showerror(
                "Unexpected Error",
                "Something went wrong. Please check the log for details.",
            )

    return wrapper

logger = logging_utils.setup_logger("app")

class _DummySignal:
    def emit(self, *args, **kwargs):
        pass


class Worker(threading.Thread):
    """Background thread that delegates work to processing_engine."""

    def __init__(self, input_path, excel_path):
        super().__init__(daemon=True)
        self.input_path = input_path
        self.excel_path = excel_path
        self.update_status = _DummySignal()
        self.update_progress = _DummySignal()
        self.finished = _DummySignal()

    def run(self):
        try:
            from importlib import import_module
            pe = import_module("processing_engine")
            run_job = pe.run_processing_job
            # Lazily access heavy helpers
            getattr(pe, "process_folder", None)
            getattr(pe, "process_zip_archive", None)

            job = {"excel_path": self.excel_path, "input_path": self.input_path}
            run_job(job, queue.Queue(), threading.Event())
            self.finished.emit("Complete")
        except Exception as exc:  # pragma: no cover - logging only
            logger.exception("Worker error", exc_info=exc)
            msg = f"Error: {exc}"
            try:
                self.update_status.emit(msg)
                self.finished.emit(msg)
            finally:
                pass

class QAApp(tk.Tk):
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
        # Update start button whenever user edits input fields
        self.selected_folder.trace_add("write", lambda *a: self.update_start_button_state())
        self.selected_excel.trace_add("write", lambda *a: self.update_start_button_state())
        self.status_current_file = tk.StringVar(value="Idle")
        self.progress_value = tk.DoubleVar(value=0)
        self.time_remaining_var = tk.StringVar(value="")
        self.count_pass, self.count_fail, self.count_review, self.count_ocr = (tk.IntVar(value=0) for _ in range(4))
        self.led_status_var = tk.StringVar(value="[Idle]")

        # --- Setup ---
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        ensure_folders()
        self.update_start_button_state()
        self.after(100, self.process_response_queue)


    def _setup_window(self):
        self.title(f"Kyocera QA ServiceNow Knowledge Tool v{VERSION}")
        self.geometry("1100x850")
        self.minsize(950, 750)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.configure(bg=BRAND_COLORS["background"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BRAND_COLORS["background"])
        style.configure("TLabel", background=BRAND_COLORS["background"], foreground=BRAND_COLORS["kyocera_black"], font=("Segoe UI", 10))
        style.configure("Header.TFrame", background=BRAND_COLORS["background"])
        style.configure("Header.TLabel", background=BRAND_COLORS["background"], foreground=BRAND_COLORS["header_text"], font=("Segoe UI", 16, "bold"))
        style.configure("KyoceraLogo.TLabel", background=BRAND_COLORS["background"], foreground=BRAND_COLORS["kyocera_red"], font=("Arial Black", 22))
        style.configure("TButton", background=BRAND_COLORS["kyocera_black"], foreground="white", font=("Segoe UI", 10, "bold"), padding=5)
        style.map("TButton", background=[("active", BRAND_COLORS["kyocera_red"])])
        style.configure("Red.TButton", background=BRAND_COLORS["kyocera_red"], foreground="white")
        style.map("Red.TButton", background=[("active", "#B81525")])
        style.configure("Status.TLabel", font=("Segoe UI", 9), background=BRAND_COLORS["frame_background"])
        style.configure("Status.Header.TLabel", font=("Segoe UI", 9, "bold"), background=BRAND_COLORS["frame_background"])
        style.configure("Dark.TFrame", background=BRAND_COLORS["frame_background"])
        style.configure("Blue.Horizontal.TProgressbar", troughcolor=BRAND_COLORS["frame_background"], background=BRAND_COLORS["accent_blue"], borderwidth=0)
        style.configure("LED.TLabel", font=("Segoe UI", 9, "bold"))
        style.configure("LEDRed.TLabel", foreground=BRAND_COLORS["kyocera_red"])
        style.configure("LEDYellow.TLabel", foreground=BRAND_COLORS["warning_yellow"])
        style.configure("LEDGreen.TLabel", foreground=BRAND_COLORS["success_green"])
        style.configure("LEDBlue.TLabel", foreground=BRAND_COLORS["accent_blue"])

    def _create_widgets(self):
        header_frame = ttk.Frame(self, style="Header.TFrame", padding=(10, 10))
        header_frame.grid(row=0, column=0, sticky="ew")
        separator = ttk.Separator(header_frame, orient='horizontal')
        separator.pack(side="bottom", fill="x")
        ttk.Label(header_frame, text="KYOCERA", style="KyoceraLogo.TLabel").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(header_frame, text="QA ServiceNow Knowledge Tool", style="Header.TLabel").pack(side=tk.LEFT, padx=(15, 0))
        
        main_frame = ttk.Frame(self, padding=15)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        self._create_io_section(main_frame)
        self._create_process_controls(main_frame)
        self._create_status_and_log_section(main_frame)

    def _create_io_section(self, parent):
        io_frame = ttk.LabelFrame(parent, text="1. Select Inputs", padding=10)
        io_frame.grid(row=0, column=0, sticky="ew", pady=5)
        io_frame.columnconfigure(1, weight=1)
        
        ttk.Label(io_frame, text="Excel File to Clone:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(io_frame, textvariable=self.selected_excel, width=80).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(io_frame, text="Browse...", command=self.browse_excel).grid(row=0, column=2, padx=5)
        
        ttk.Label(io_frame, text="Process Folder:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        ttk.Entry(io_frame, textvariable=self.selected_folder, width=80).grid(row=1, column=1, sticky="ew", padx=5)
        ttk.Button(io_frame, text="Browse...", command=self.browse_folder).grid(row=1, column=2, padx=5)
        
        ttk.Label(io_frame, text="Or Select PDFs:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.files_label = ttk.Label(io_frame, text="0 files selected")
        self.files_label.grid(row=2, column=1, sticky="w", padx=5)
        ttk.Button(io_frame, text="Select...", command=self.browse_files).grid(row=2, column=2, padx=5)

    def _create_process_controls(self, parent):
        controls_frame = ttk.LabelFrame(parent, text="2. Process & Manage", padding=10)
        controls_frame.grid(row=1, column=0, sticky="ew", pady=5)
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        
        self.process_btn = ttk.Button(
            controls_frame,
            text="▶ START PROCESSING",
            command=self.start_processing,
            style="Red.TButton",
            padding=(10, 8),
            state=tk.DISABLED,
        )
        self.process_btn.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        self.pause_btn = ttk.Button(controls_frame, text="⏯️ Pause", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.stop_btn = ttk.Button(controls_frame, text="⏹️ Stop Process", command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.rerun_btn = ttk.Button(controls_frame, text="🔄 Re-run Flagged Files", command=self.rerun_flagged_job, state=tk.DISABLED)
        self.rerun_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        self.open_result_btn = ttk.Button(controls_frame, text="📂 Open Result", command=self.open_result, state=tk.DISABLED)
        self.open_result_btn.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.review_btn = ttk.Button(controls_frame, text="⚙️ Pattern Manager", command=self.open_pattern_manager)
        self.review_btn.grid(row=2, column=2, padx=5, pady=5, sticky="ew")

        self.exit_btn = ttk.Button(controls_frame, text="❌ Exit", command=self.on_closing)
        self.exit_btn.grid(row=2, column=3, padx=5, pady=5, sticky="ew")

    def update_start_button_state(self):
        """Enable the start button only when required inputs are selected."""
        excel = self.selected_excel.get()
        has_pdfs = bool(self.selected_folder.get() or self.selected_files_list)
        if excel and has_pdfs:
            self.process_btn.config(state=tk.NORMAL)
        else:
            self.process_btn.config(state=tk.DISABLED)

    def _create_status_and_log_section(self, parent):
        container = ttk.LabelFrame(parent, text="3. Live Status & Activity Log", padding=10)
        container.grid(row=2, column=0, sticky="nsew", pady=5)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)
        status_frame = ttk.Frame(container, style="Dark.TFrame", padding=10)
        status_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        status_frame.columnconfigure(2, weight=1)
        ttk.Label(status_frame, text="Current File:", style="Status.Header.TLabel").grid(row=0, column=0, sticky="w", padx=5)
        self.led_label = ttk.Label(status_frame, textvariable=self.led_status_var, style="LED.TLabel", anchor="w")
        self.led_label.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(status_frame, textvariable=self.status_current_file, style="Status.TLabel", anchor="w").grid(row=0, column=2, sticky="ew", padx=5)
        ttk.Label(status_frame, text="Overall Progress:", style="Status.Header.TLabel").grid(row=1, column=0, sticky="w", padx=5)
        self.progress_bar = ttk.Progressbar(status_frame, orient='horizontal', mode='determinate', variable=self.progress_value, style="Blue.Horizontal.TProgressbar")
        self.progress_bar.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=(10,5))
        ttk.Label(status_frame, textvariable=self.time_remaining_var, style="Status.TLabel", anchor="e").grid(row=1, column=3, sticky="e", padx=10)
        summary_frame = ttk.Frame(container, style="Dark.TFrame", padding=10)
        summary_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(5,0))
        ttk.Label(summary_frame, text="Pass:", style="Status.Header.TLabel").pack(side="left", padx=(10,2))
        ttk.Label(summary_frame, textvariable=self.count_pass, style="Status.TLabel", foreground=BRAND_COLORS["success_green"]).pack(side="left", padx=(0,10))
        ttk.Label(summary_frame, text="Fail:", style="Status.Header.TLabel").pack(side="left", padx=(10,2))
        ttk.Label(summary_frame, textvariable=self.count_fail, style="Status.TLabel", foreground=BRAND_COLORS["kyocera_red"]).pack(side="left", padx=(0,10))
        ttk.Label(summary_frame, text="Needs Review:", style="Status.Header.TLabel").pack(side="left", padx=(10,2))
        ttk.Label(summary_frame, textvariable=self.count_review, style="Status.TLabel", foreground=BRAND_COLORS["warning_yellow"]).pack(side="left", padx=(0,10))
        ttk.Label(summary_frame, text="OCR Used:", style="Status.Header.TLabel").pack(side="left", padx=(10,2))
        ttk.Label(summary_frame, textvariable=self.count_ocr, style="Status.TLabel", foreground=BRAND_COLORS["accent_blue"]).pack(side="left", padx=(0,10))
        review_frame = ttk.Frame(container, style="Dark.TFrame", padding=(5, 10))
        review_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(5,0))
        review_frame.columnconfigure(0, weight=1)
        review_header_frame = ttk.Frame(review_frame, style="Dark.TFrame")
        review_header_frame.pack(fill="x", expand=True)
        ttk.Label(review_header_frame, text="Files Flagged for Review:", style="Status.Header.TLabel").pack(side="left")
        self.review_file_btn = ttk.Button(review_header_frame, text="Review Selected File", command=self.open_review_for_selected_file, state=tk.DISABLED)
        self.review_file_btn.pack(side="right")
        self.review_tree = ttk.Treeview(review_frame, columns=('filename', 'reason'), show='headings', height=3)
        self.review_tree.pack(fill="x", expand=True, pady=(5,0))
        self.review_tree.heading('filename', text='File Name')
        self.review_tree.heading('reason', text='Reason')
        self.review_tree.column('filename', width=400)
        self.review_tree.bind("<<TreeviewSelect>>", self.on_review_file_select)
        log_text_frame = ttk.Frame(container)
        log_text_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
        log_text_frame.rowconfigure(0, weight=1)
        log_text_frame.columnconfigure(0, weight=1)
        self.log_text = tk.Text(log_text_frame, height=8, wrap=tk.WORD, state=tk.DISABLED, bg="white", relief="solid", borderwidth=1, font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scrollbar = ttk.Scrollbar(log_text_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        for tag, color_key in [("info", "accent_blue"), ("success", "success_green"), ("warning", "warning_yellow"), ("error", "kyocera_red")]:
            self.log_text.tag_configure(tag, foreground=BRAND_COLORS[color_key])

    @gui_callback
    def start_processing(self, job_request=None, is_rerun=False):
        if self.is_processing:
            return
        if not job_request:
            input_path = self.selected_folder.get() or self.selected_files_list
            if not input_path:
                messagebox.showwarning("Input Missing", "Please select files or a folder.")
                return
            excel_path = self.selected_excel.get()
            if not excel_path:
                messagebox.showwarning("Input Missing", "Please select a base Excel file.")
                return
            job_request = {"excel_path": excel_path, "input_path": input_path}
            self.last_run_info = job_request
        job_request["is_rerun"] = is_rerun
        job_request["pause_event"] = self.pause_event
        self.update_ui_for_processing_start()
        self.log_message("Starting processing job...", "info")
        self.start_time = time.time()
        self.processing_thread = threading.Thread(
            target=self.run_job_with_error_handling,
            args=(job_request,),
            daemon=True,
        )
        self.processing_thread.start()

    def run_job_with_error_handling(self, job_request):
        """Run processing job safely inside a worker thread."""
        try:
            run_processing_job(job_request, self.response_queue, self.cancel_event)
        except Exception as exc:  # pragma: no cover - defensive
            logging_utils.log_exception(logger, "Processing job failed")
            messagebox.showerror(
                "Processing Error",
                "Processing failed. Please check the log for details.",
            )
            self.response_queue.put({"type": "finish", "status": f"Error: {exc}"})

    @gui_callback
    def stop_processing(self):
        if not self.is_processing: return
        if messagebox.askokcancel("Stop Process", "Are you sure you want to stop the current process?"):
            self.log_message("Stopping process...", "warning")
            self.cancel_event.set()

    @gui_callback
    def toggle_pause(self):
        if not self.is_processing: return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_event.set()
            self.pause_btn.config(text="⏯️ Resume")
            self.log_message("Processing paused.", "warning")
        else:
            self.pause_event.clear()
            self.pause_btn.config(text="⏯️ Pause")
            self.log_message("Processing resumed.", "info")

    @gui_callback
    def rerun_flagged_job(self):
        if not self.reviewable_files:
            messagebox.showwarning("No Files to Re-run", "There are no files currently flagged for review.")
            return
        if not self.result_file_path:
            messagebox.showerror("Error", "Could not find the previous result file to update.")
            return
        files_to_rerun = [item['pdf_path'] for item in self.reviewable_files]
        self.log_message(f"Re-running process on {len(files_to_rerun)} flagged file(s)...", "info")
        job_request = {"excel_path": self.result_file_path, "input_path": files_to_rerun}
        self.start_processing(job_request=job_request, is_rerun=True)

    def on_review_file_select(self, event):
        if self.review_tree.focus():
            self.review_file_btn.config(state=tk.NORMAL)
        else:
            self.review_file_btn.config(state=tk.DISABLED)

    @gui_callback
    def open_review_for_selected_file(self):
        selected_item = self.review_tree.focus()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a file from the review list first.")
            return
        selected_filename = self.review_tree.item(selected_item)['values'][0]
        file_to_review = next((f for f in self.reviewable_files if f['filename'] == selected_filename), None)
        if file_to_review:
            ReviewWindow(self, "MODEL_PATTERNS", "Model Recognition Patterns", file_to_review)
        else:
            messagebox.showerror("Error", "Could not find the details for the selected file.")

    @gui_callback
    def open_pattern_manager(self):
        dialog = tk.Toplevel(self)
        dialog.title("Pattern Manager")
        dialog.geometry("350x150")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        ttk.Label(dialog, text="Which set of patterns would you like to manage?", wraplength=300).pack(pady=15)
        btn_container = ttk.Frame(dialog)
        btn_container.pack(pady=10)
        def launch_review(pattern_name, pattern_label):
            dialog.destroy()
            ReviewWindow(self, pattern_name, pattern_label, file_info=None)
        ttk.Button(btn_container, text="Model Patterns", command=lambda: launch_review("MODEL_PATTERNS", "Model Recognition Patterns")).pack(side="left", padx=10)
        ttk.Button(btn_container, text="QA Number Patterns", command=lambda: launch_review("QA_NUMBER_PATTERNS", "QA Number Patterns")).pack(side="left", padx=10)
    
    def process_response_queue(self):
        try:
            while True:
                response = self.response_queue.get_nowait()
                msg_type = response.get("type")
                if msg_type == "status":
                    self.status_current_file.set(response.get("msg", "Idle"))
                    self.set_led_status(response.get("led"))
                elif msg_type == "increment_counter":
                    counter_var = getattr(self, f"count_{response['counter']}", None)
                    if counter_var: counter_var.set(counter_var.get() + 1)
                elif msg_type == "file_complete":
                    status = response.get("status")
                    if status == "Pass": self.count_pass.set(self.count_pass.get() + 1)
                    elif status == "Fail": self.count_fail.set(self.count_fail.get() + 1)
                    elif status == "Needs Review": self.count_review.set(self.count_review.get() + 1)
                elif msg_type == "log": self.log_message(response["msg"], response["tag"])
                elif msg_type == "progress":
                    current_item, total_items = response["current"], response["total"]
                    if total_items > 0:
                        percent_done = current_item / total_items
                        self.progress_value.set(percent_done * 100)
                        if self.start_time and current_item > 1:
                            elapsed_time = time.time() - self.start_time
                            total_estimated_time = elapsed_time / percent_done
                            remaining_time = total_estimated_time - elapsed_time
                            self.time_remaining_var.set(self.format_time(remaining_time))
                elif msg_type == "review_item":
                    filename_to_find = response["data"]["filename"]
                    if not any(item["filename"] == filename_to_find for item in self.reviewable_files):
                         self.reviewable_files.append(response["data"])
                elif msg_type == "result_path": self.result_file_path = response["path"]
                elif msg_type == "finish": self.update_ui_after_finish(response)
        except queue.Empty: pass
        finally: self.after(100, self.process_response_queue)
    
    def update_ui_after_finish(self, response):
        self.is_processing = False
        self.is_paused = False
        self.cancel_event.clear()
        self.progress_value.set(100)
        self.time_remaining_var.set("Complete!")
        self.status_current_file.set("Idle")
        self.set_led_status("Idle")
        self.review_tree.delete(*self.review_tree.get_children())
        for item in self.reviewable_files:
            self.review_tree.insert('', 'end', values=(item['filename'], item['reason']))
        self.process_btn.config(state=tk.NORMAL)
        self.rerun_btn.config(state=tk.NORMAL if self.reviewable_files else tk.DISABLED)
        self.review_file_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.NORMAL)
        self.review_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        if self.result_file_path: self.open_result_btn.config(state=tk.NORMAL)
        self.log_message(f"Processing finished. Status: {response['status']}", "success" if response['status'] == 'Complete' else 'error')

    def update_ui_for_processing_start(self):
        self.is_processing = True
        self.is_paused = False
        self.pause_event.clear()
        self.process_btn.config(state=tk.DISABLED)
        self.rerun_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.DISABLED)
        self.open_result_btn.config(state=tk.DISABLED)
        self.review_btn.config(state=tk.DISABLED)
        self.review_file_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text="⏯️ Pause")
        self.stop_btn.config(state=tk.NORMAL)
        self.status_current_file.set("Initializing...")
        self.time_remaining_var.set("Calculating...")
        self.progress_value.set(0)
        self.count_pass.set(0); self.count_fail.set(0); self.count_review.set(0); self.count_ocr.set(0)
        self.reviewable_files.clear()
        self.review_tree.delete(*self.review_tree.get_children())
        
    def set_led_status(self, status: str):
        if not status: self.led_status_var.set(""); return
        text_map = {"Queued": "[Queued]", "OCR": "[OCR...]", "AI": "[AI...]", "Saving": "[Saving]", "Setup": "[Setup]", "Paused": "[Paused]"}
        color_map = {"OCR": "LEDBlue", "AI": "LEDBlue", "Fail": "LEDRed", "Pass": "LEDGreen", "Needs Review": "LEDYellow", "Paused": "LEDYellow"}
        self.led_status_var.set(text_map.get(status, f"[{status}]"))
        style_name = color_map.get(status, "LED") + ".TLabel"
        self.led_label.configure(style=style_name)
        
    def format_time(self, seconds):
        if seconds < 0: return ""
        if seconds < 60: return f"{int(seconds)}s remaining"
        minutes, seconds_part = divmod(int(seconds), 60)
        return f"{minutes}m {seconds_part}s remaining"
            
    def log_message(self, msg, tag):
        try:
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
            if tag == "error": logger.error(msg)
            else: logger.info(msg)
        except Exception as e:
            print(f"Failed to log message: {e}")

    @gui_callback
    def on_closing(self):
        if self.is_processing:
            if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit while a process is running?"):
                self.cancel_event.set()
                self.destroy()
        else:
            self.destroy()
        cleanup_temp_files()
        
    @gui_callback
    def browse_excel(self):
        path = filedialog.askopenfilename(title="Select ServiceNow Excel File to Clone", filetypes=[("Excel Files", "*.xlsx")])
        if path:
            self.selected_excel.set(path)
        self.update_start_button_state()
            
    @gui_callback
    def browse_folder(self):
        path = filedialog.askdirectory(title="Select Folder Containing PDFs")
        if path:
            self.selected_folder.set(path)
            self.selected_files_list.clear()
            self.files_label.config(text="0 files selected")
        self.update_start_button_state()
    
    @gui_callback
    def browse_files(self):
        paths = filedialog.askopenfilenames(title="Select PDF or ZIP Files", filetypes=[("PDF/ZIP Files", "*.pdf *.zip")])
        if paths:
            self.selected_files_list = list(paths)
            self.files_label.config(text=f"{len(paths)} file(s) selected")
            self.selected_folder.set("")
        self.update_start_button_state()
#==============================================================
# --- THIS METHOD WAS MISSING ---
#==============================================================
    @gui_callback
    def open_result(self):
        """Opens the last generated Excel file with the default application."""
        if self.result_file_path and Path(self.result_file_path).exists():
            try:
                open_file(self.result_file_path)
                self.log_message(f"Opened result file: {self.result_file_path}", "info")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open the file.\n\nError: {e}")
                self.log_message(f"Failed to open result file: {e}", "error")
        else:
            messagebox.showwarning("File Not Found", "The result file could not be found. It may have been moved or deleted.")
#==============================================================
# --- END OF FIX ---
#==============================================================

KyoQAToolApp = QAApp

if __name__ == "__main__":
    app = QAApp()
    app.mainloop()
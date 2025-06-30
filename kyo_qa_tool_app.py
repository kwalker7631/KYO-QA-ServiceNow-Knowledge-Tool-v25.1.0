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
        # Alias for compatibility
        self.count_needs_review = self.count_review

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
        self.status_current_file = tk.StringVar(value="Ready to process")
        self.progress_value = tk.DoubleVar(value=0)
        self.time_remaining_var = tk.StringVar(value="")
        self.led_status_var = tk.StringVar(value="●")

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
        self.geometry("1200x900")
        self.minsize(1000, 800)

        # Set window icon if available
        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(icon_path)
        except:
            pass

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.configure(bg=BRAND_COLORS["background"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Configure ttk styles
        self.style.theme_use("clam")

        # Frame styles
        self.style.configure("TFrame", background=BRAND_COLORS["background"])
        self.style.configure("Header.TFrame", background=BRAND_COLORS["background"])
        self.style.configure("Status.TFrame", background="#f0f0f0", relief="sunken", borderwidth=1)
        self.style.configure("Summary.TFrame", background="#f8f8f8", relief="flat")
        self.style.configure("Review.TFrame", background="#f8f8f8", relief="flat")

        # Label styles
        self.style.configure("TLabel", background=BRAND_COLORS["background"], font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("Status.TLabel", background="#f0f0f0", font=("Segoe UI", 10))
        self.style.configure("Status.Header.TLabel", background="#f0f0f0", font=("Segoe UI", 10, "bold"))
        self.style.configure("LED.TLabel", background="#f0f0f0", font=("Segoe UI", 12))

        # Counter label styles
        self.style.configure("Count.Green.TLabel", background="#f8f8f8", foreground=BRAND_COLORS["success_green"])
        self.style.configure("Count.Red.TLabel", background="#f8f8f8", foreground=BRAND_COLORS["kyocera_red"])
        self.style.configure("Count.Orange.TLabel", background="#f8f8f8", foreground="#ff8c00")
        self.style.configure("Count.Blue.TLabel", background="#f8f8f8", foreground=BRAND_COLORS["accent_blue"])

        # Button styles
        self.style.configure("TButton", font=("Segoe UI", 10), padding=6)
        self.style.map("TButton",
            background=[('active', '#e0e0e0'), ('!active', '#f0f0f0')],
            foreground=[('active', 'black'), ('!active', 'black')]
        )

        # Red button style for main action
        self.style.configure("Red.TButton", font=("Segoe UI", 12, "bold"), foreground="white")
        self.style.map("Red.TButton",
            background=[('active', '#cc0025'), ('!active', BRAND_COLORS["kyocera_red"])],
            foreground=[('active', 'white'), ('!active', 'white')]
        )

        # Other widget styles
        self.style.configure("TEntry", fieldbackground="white", borderwidth=1, relief="solid")
        self.style.configure("TLabelFrame", background=BRAND_COLORS["background"], font=("Segoe UI", 11, "bold"))
        self.style.configure("Blue.Horizontal.TProgressbar", background=BRAND_COLORS["accent_blue"])
        self.style.configure("Treeview", font=("Segoe UI", 9))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _create_widgets(self):
        create_main_header(self, VERSION, BRAND_COLORS)

        # Main container
        main_frame = ttk.Frame(self, padding=20)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Create sections
        create_io_section(main_frame, self)
        create_process_controls(main_frame, self)
        create_status_and_log_section(main_frame, self)

    def start_processing(self, job=None, is_rerun=False):
        if self.is_processing:
            return

        if not job:
            input_path = self.selected_folder.get() or self.selected_files_list
            if not input_path:
                messagebox.showwarning("Input Missing", "Please select files or a folder.")
                return
            excel_path = self.selected_excel.get()
            if not excel_path:
                messagebox.showwarning("Input Missing", "Please select a base Excel file.")
                return
            job = {"excel_path": excel_path, "input_path": input_path}
            self.last_run_info = job

        job["is_rerun"] = is_rerun
        job["pause_event"] = self.pause_event

        self.update_ui_for_start()
        self.log_message("Starting processing job...", "info")
        self.start_time = time.time()

        # Start processing in background thread
        threading.Thread(
            target=run_processing_job,
            args=(job, self.response_queue, self.cancel_event, self.pause_event),
            daemon=True
        ).start()

    def rerun_flagged_job(self):
        if not self.reviewable_files:
            messagebox.showwarning("No Files", "No files need re-running.")
            return
        if not self.result_file_path:
            messagebox.showerror("Error", "Previous result file not found.")
            return

        files = [item["pdf_path"] for item in self.reviewable_files]
        self.log_message(f"Re-running {len(files)} flagged files...", "info")
        self.start_processing(
            job={"excel_path": self.result_file_path, "input_path": files},
            is_rerun=True
        )

    def browse_excel(self):
        path = filedialog.askopenfilename(
            title="Select Excel Template",
            filetypes=[("Excel Files", "*.xlsx *.xlsm"), ("All Files", "*.*")],
        )
        if path:
            self.selected_excel.set(path)
            self.log_message(f"Excel selected: {Path(path).name}", "info")

    def browse_folder(self):
        path = filedialog.askdirectory(title="Select Folder with PDFs")
        if path:
            self.selected_folder.set(path)
            self.selected_files_list = []
            pdf_count = len(list(Path(path).glob("*.pdf")))
            self.files_label.config(text=f"{pdf_count} PDFs in folder")
            self.log_message(f"Folder selected: {path} ({pdf_count} PDFs)", "info")

    def browse_files(self):
        paths = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
        )
        if paths:
            self.selected_files_list = list(paths)
            self.selected_folder.set("")
            self.files_label.config(text=f"{len(paths)} files selected")
            self.log_message(f"{len(paths)} PDF files selected", "info")

    def toggle_pause(self):
        if not self.is_processing:
            return

        if self.is_paused:
            self.is_paused = False
            self.pause_event.clear()
            self.pause_btn.config(text="⏯️ Pause")
            self.log_message("Processing resumed", "info")
            self.set_led("Processing")
        else:
            self.is_paused = True
            self.pause_event.set()
            self.pause_btn.config(text="▶️ Resume")
            self.log_message("Processing paused", "warning")
            self.set_led("Paused")

    def stop_processing(self):
        if not self.is_processing:
            return

        if messagebox.askyesno("Confirm Stop", "Stop the current processing job?"):
            self.cancel_event.set()
            self.log_message("Stopping processing...", "warning")
            self.set_led("Stopping")

    def on_closing(self):
        if self.is_processing:
            if not messagebox.askyesno("Exit", "Processing is running. Exit anyway?"):
                return
            self.cancel_event.set()
            time.sleep(0.5)  # Give thread time to stop

        cleanup_temp_files()
        self.destroy()

    def open_result(self):
        if self.result_file_path and Path(self.result_file_path).exists():
            try:
                open_file(self.result_file_path)
                self.log_message(f"Opened result file: {Path(self.result_file_path).name}", "info")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
        else:
            messagebox.showwarning("Not Found", "Result file not found or has been moved.")

    def open_pattern_manager(self):
        # Create selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select Pattern Type")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        ttk.Label(dialog, text="Which patterns do you want to manage?", font=("Segoe UI", 10)).pack(pady=20)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def open_model_patterns():
            dialog.destroy()
            file_info = self.reviewable_files[0] if self.reviewable_files else None
            ReviewWindow(self, "MODEL_PATTERNS", "Model Patterns", file_info)

        def open_qa_patterns():
            dialog.destroy()
            file_info = self.reviewable_files[0] if self.reviewable_files else None
            ReviewWindow(self, "QA_NUMBER_PATTERNS", "QA Number Patterns", file_info)

        ttk.Button(button_frame, text="Model Patterns", command=open_model_patterns).pack(side="left", padx=10)
        ttk.Button(button_frame, text="QA Patterns", command=open_qa_patterns).pack(side="left", padx=10)

    def log_message(self, message, level="info"):
        timestamp = time.strftime("%H:%M:%S")

        # Log to file
        getattr(logger, level, logger.info)(message)

        # Log to GUI
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def set_led(self, status):
        # Set LED color based on status
        led_colors = {
            "Idle": ("●", "#808080"),
            "Ready": ("●", BRAND_COLORS["success_green"]),
            "Processing": ("●", BRAND_COLORS["accent_blue"]),
            "OCR": ("●", "#1E90FF"),
            "AI": ("●", "#9370DB"),
            "Paused": ("●", "#FFA500"),
            "Stopping": ("●", "#FF6347"),
            "Error": ("●", BRAND_COLORS["kyocera_red"]),
            "Complete": ("●", BRAND_COLORS["success_green"]),
            "Queued": ("●", "#808080"),
            "Saving": ("●", "#32CD32"),
            "Pass": ("●", BRAND_COLORS["success_green"]),
            "Fail": ("●", BRAND_COLORS["kyocera_red"]),
            "Needs Review": ("●", "#FFA500")
        }

        symbol, color = led_colors.get(status, ("●", "#808080"))
        self.led_status_var.set(symbol)
        self.led_label.config(foreground=color)

    def update_ui_for_start(self):
        self.is_processing = True
        self.is_paused = False
        self.cancel_event.clear()
        self.pause_event.clear()

        # Reset counters
        for var in [self.count_pass, self.count_fail, self.count_review, self.count_ocr]:
            var.set(0)

        # Clear review list
        self.reviewable_files.clear()
        self.review_tree.delete(*self.review_tree.get_children())

        # Update button states
        self.process_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text="⏯️ Pause")
        self.stop_btn.config(state=tk.NORMAL)
        self.review_btn.config(state=tk.DISABLED)
        self.open_result_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.DISABLED)
        self.rerun_btn.config(state=tk.DISABLED)
        self.review_file_btn.config(state=tk.DISABLED)

        # Update status
        self.status_current_file.set("Initializing...")
        self.time_remaining_var.set("Calculating...")
        self.progress_value.set(0)
        self.set_led("Processing")

    def update_ui_for_finish(self):
        self.is_processing = False
        self.is_paused = False
        self.pause_event.clear()
        self.cancel_event.clear()

        # Update button states
        self.process_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="⏯️ Pause")
        self.stop_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.NORMAL)
        self.review_btn.config(state=tk.NORMAL)

        if self.result_file_path:
            self.open_result_btn.config(state=tk.NORMAL)

        if self.reviewable_files:
            self.rerun_btn.config(state=tk.NORMAL)

        # Update status
        self.status_current_file.set("Processing complete")
        self.time_remaining_var.set("Done!")
        self.set_led("Complete")

    def on_review_file_select(self, event):
        selection = self.review_tree.selection()
        if selection:
            self.review_file_btn.config(state=tk.NORMAL)
        else:
            self.review_file_btn.config(state=tk.DISABLED)

    def open_review_for_selected_file(self):
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to review.")
            return

        # In a Treeview, the item ID is what's returned by selection()
        item_id = selection[0]
        # To get the filename (which we stored in the 'values' tuple), we use item()
        filename = self.review_tree.item(item_id, "values")[0]

        # Find the review info for this file
        review_info = next((f for f in self.reviewable_files if f['filename'] == filename), None)
        if review_info:
            ReviewWindow(self, "MODEL_PATTERNS", "Model Patterns", review_info)
        else:
            messagebox.showerror("Error", "Could not find review information for the selected file.")

    def update_progress(self, current, total):
        if total > 0:
            percent = (current / total) * 100
            self.progress_value.set(percent)

            # Calculate time remaining
            if self.start_time and current > 0:
                elapsed = time.time() - self.start_time
                rate = current / elapsed
                remaining = (total - current) / rate if rate > 0 else 0

                if remaining > 60:
                    self.time_remaining_var.set(f"{int(remaining/60)}m {int(remaining%60)}s left")
                else:
                    self.time_remaining_var.set(f"{int(remaining)}s left")

    def handle_finished_job(self, status):
        elapsed = time.time() - self.start_time if self.start_time else 0
        minutes = int(elapsed / 60)
        seconds = int(elapsed % 60)

        self.log_message(f"Job finished: {status} (Time: {minutes}m {seconds}s)", "success" if status == "Complete" else "error")
        self.update_ui_for_finish()

        # Update progress to 100%
        self.progress_value.set(100)

    def process_response_queue(self):
        """Process messages from the background thread."""
        try:
            while not self.response_queue.empty():
                msg = self.response_queue.get_nowait()
                mtype = msg.get("type")

                if mtype == "log":
                    self.log_message(msg.get("msg", ""), msg.get("tag", "info"))

                elif mtype == "status":
                    self.status_current_file.set(msg.get("msg", ""))
                    if "led" in msg:
                        self.set_led(msg["led"])

                elif mtype == "progress":
                    self.update_progress(msg.get("current", 0), msg.get("total", 1))

                elif mtype == "increment_counter":
                    counter_name = msg.get("counter")
                    var = getattr(self, f"count_{counter_name}", None)
                    if var and isinstance(var, tk.IntVar):
                        var.set(var.get() + 1)

                elif mtype == "file_complete":
                    status = msg.get("status", "").lower().replace(" ", "_")
                    var = getattr(self, f"count_{status}", None)
                    if var and isinstance(var, tk.IntVar):
                        var.set(var.get() + 1)

                elif mtype == "review_item":
                    data = msg.get("data", {})
                    self.reviewable_files.append(data)
                    # --- BUG FIX ---
                    # Use the 'values' parameter to populate the visible column.
                    # The 'text' parameter populates the hidden tree column (#0).
                    filename = data.get('filename', 'Unknown')
                    self.review_tree.insert('', 'end', values=(filename,))
                    # --- END OF BUG FIX ---

                elif mtype == "result_path":
                    self.result_file_path = msg.get("path")

                elif mtype == "finish":
                    self.handle_finished_job(msg.get("status", "Complete"))

        except queue.Empty:
            pass
        except Exception as e:
            self.log_message(f"Error processing queue: {e}", "error")

        # Schedule next check
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
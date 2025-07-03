# kyo_qa_tool_app.py
# Version: 26.0.0
# Last modified: 2025-07-03
# Main GUI application for the KYO QA Tool with full processing functionality

import json
import threading
import time
from pathlib import Path
from queue import Queue, Empty
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
import os

from config import (
    BRAND_COLORS,
    PDF_TXT_DIR,
    NEED_REVIEW_DIR,
    CACHE_DIR,
    ASSETS_DIR,
    OUTPUT_DIR,
)
from gui_components import (
    create_main_header,
    create_io_section,
    create_process_controls,
    create_status_and_log_section,
)
from version import get_version
from logging_utils import setup_logger, log_info, log_warning, log_error
from file_utils import ensure_folders
from kyo_review_tool import ReviewWindow

__all__ = ["KyoQAToolApp", "TextRedirector"]


# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------
class TextRedirector:
    """Simple file-like object that redirects written text to a queue."""

    def __init__(self, queue: Queue):
        self.queue = queue

    def write(self, text: str) -> None:
        if text:
            self.queue.put(text)

    def flush(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Basic icon utilities used by the application.
# ---------------------------------------------------------------------------

ICON_MAP = {
    "start": "start.png",
    "pause": "pause.png", 
    "stop": "stop.png",
    "rerun": "rerun.png",
    "open": "open.png",
    "browse": "browse.png",
    "patterns": "patterns.png",
    "exit": "exit.png",
    "fullscreen": "fullscreen.png",
}


def load_icon(name: str) -> tk.PhotoImage | None:
    path = ASSETS_DIR / name
    try:
        return tk.PhotoImage(file=path) if path.exists() else None
    except Exception:
        return None


def get_text_icon(key: str) -> str:
    """Return a small unicode fallback for a given icon key."""
    fallbacks = {
        "start": "▶",
        "pause": "❚❚", 
        "stop": "■",
        "rerun": "↺",
        "open": "⌗",
        "browse": "…",
        "patterns": "⧉",
        "exit": "✖",
        "fullscreen": "⛶",
    }
    return fallbacks.get(key, "")


def create_default_icons() -> bool:
    """Ensure the assets folder exists. Return True if any png files exist."""
    ASSETS_DIR.mkdir(exist_ok=True)
    return any((ASSETS_DIR / fname).exists() for fname in ICON_MAP.values())


# ---------------------------------------------------------------------------
# Application class
# ---------------------------------------------------------------------------
class KyoQAToolApp(tk.Tk):
    """Main GUI application for the KYO QA Tool."""

    def __init__(self) -> None:
        super().__init__()
        self.title("KYO QA Knowledge Tool")
        self.geometry("1000x700")
        self.configure(bg=BRAND_COLORS["background"])

        # --- Processing state variables ---
        self.processing = False
        self.paused = False
        self.progress_queue = Queue()
        self.cancel_event = threading.Event()
        self.pause_event = threading.Event()
        self.worker_thread = None
        self.result_file_path = None
        self.last_run_info = {}

        # --- UI Variables ---
        self.selected_excel = tk.StringVar()
        self.selected_folder = tk.StringVar()
        self.selected_files = []
        self.progress_value = tk.DoubleVar(value=0.0)
        self.status_current_file = tk.StringVar(value="Ready")
        self.time_remaining_var = tk.StringVar(value="")
        self.led_status_var = tk.StringVar(value="● Idle")
        self.count_pass = tk.IntVar(value=0)
        self.count_fail = tk.IntVar(value=0)
        self.count_review = tk.IntVar(value=0)
        self.count_ocr = tk.IntVar(value=0)

        # --- Progress tracking ---
        self.start_time = None
        self.current_file_index = 0
        self.total_files = 0

        # --- Setup logging ---
        self.log_queue: Queue[str] = Queue()
        self.logger = setup_logger("app", log_widget=None)

        # --- Create required directories ---
        ensure_folders()

        # --- Load icons with graceful fallback ---
        try:
            icons_available = create_default_icons()
            for key, filename in ICON_MAP.items():
                setattr(self, f"{key}_icon", load_icon(filename) if icons_available else None)
        except Exception:
            for key in ICON_MAP:
                setattr(self, f"{key}_icon", None)

        # --- Configure styles ---
        self._configure_styles()

        # --- Build UI ---
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)

        create_main_header(container, get_version(), BRAND_COLORS)
        create_io_section(container, self)
        create_process_controls(container, self)
        create_status_and_log_section(container, self)

        # --- Start progress queue monitor ---
        self.after(100, self.process_progress_queue)

        # --- Handle window close ---
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        log_info(self.logger, "KYO QA Tool initialized successfully")

    def _configure_styles(self):
        """Configure custom styles for the application."""
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure button styles
        style.configure("Red.TButton", foreground="white", background=BRAND_COLORS["kyocera_red"])
        style.map("Red.TButton", background=[("active", "#c41e3a")])
        
        # Configure LED status style
        style.configure("LED.TLabel", foreground=BRAND_COLORS["success_green"], font=("Consolas", 10, "bold"))
        
        # Configure status label styles
        style.configure("Status.TLabel", font=("Segoe UI", 9))
        style.configure("Status.Header.TLabel", font=("Segoe UI", 9, "bold"))
        
        # Configure count label styles
        for color in ["Green", "Red", "Orange", "Blue"]:
            color_value = BRAND_COLORS.get(f"count_{color.lower()}", BRAND_COLORS["header_text"])
            style.configure(f"Count.{color}.TLabel", foreground=color_value, font=("Segoe UI", 10, "bold"))

    # ------------------------------------------------------------------
    # File selection methods
    # ------------------------------------------------------------------
    def browse_excel(self) -> None:
        """Browse for Excel template file."""
        file_path = filedialog.askopenfilename(
            title="Select Excel Template",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.selected_excel.set(file_path)
            log_info(self.logger, f"Selected Excel file: {Path(file_path).name}")

    def browse_folder(self) -> None:
        """Browse for folder containing PDF files."""
        folder_path = filedialog.askdirectory(title="Select Folder with PDF Files")
        if folder_path:
            self.selected_folder.set(folder_path)
            self.selected_files = []  # Clear individual file selection
            
            # Count PDF files in folder
            pdf_count = len(list(Path(folder_path).glob("*.pdf")))
            log_info(self.logger, f"Selected folder: {Path(folder_path).name} ({pdf_count} PDFs)")

    def browse_files(self) -> None:
        """Browse for individual PDF files."""
        file_paths = filedialog.askopenfilenames(
            title="Select PDF Files",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if file_paths:
            self.selected_files = list(file_paths)
            self.selected_folder.set("")  # Clear folder selection
            log_info(self.logger, f"Selected {len(file_paths)} individual PDF files")

    # ------------------------------------------------------------------
    # Processing control methods
    # ------------------------------------------------------------------
    def start_processing(self) -> None:
        """Start the PDF processing job."""
        if self.processing:
            return

        # Validate inputs
        if not self.selected_excel.get():
            messagebox.showerror("Input Required", "Please select an Excel file.")
            return

        if not self.selected_folder.get() and not self.selected_files:
            messagebox.showerror("Input Required", "Please select a folder or PDF files to process.")
            return

        if not Path(self.selected_excel.get()).exists():
            messagebox.showerror("File Not Found", "The selected Excel file does not exist.")
            return

        # Prepare job info
        job_info = {
            "excel_path": self.selected_excel.get(),
            "input_path": self.selected_folder.get() if self.selected_folder.get() else self.selected_files,
            "is_rerun": False
        }

        self._start_worker_thread(job_info)

    def toggle_pause(self) -> None:
        """Toggle pause/resume of processing."""
        if not self.processing:
            return

        self.paused = not self.paused
        if self.paused:
            self.pause_event.set()
            self.pause_btn.config(text=" Resume", image=self.start_icon)
            self.led_status_var.set("● Paused")
            log_info(self.logger, "Processing paused")
        else:
            self.pause_event.clear()
            self.pause_btn.config(text=" Pause", image=self.pause_icon)
            self.led_status_var.set("● Processing")
            log_info(self.logger, "Processing resumed")

    def stop_processing(self) -> None:
        """Stop the current processing job."""
        if not self.processing:
            return

        if messagebox.askyesno("Stop Processing", "Are you sure you want to stop processing?"):
            self.cancel_event.set()
            self.led_status_var.set("● Stopping...")
            log_info(self.logger, "Processing stop requested")

    def rerun_flagged_job(self) -> None:
        """Re-run processing on files that were flagged for review."""
        if self.processing:
            messagebox.showwarning("Processing Active", "Please wait for current processing to complete.")
            return

        if not self.last_run_info:
            messagebox.showinfo("No Previous Run", "No previous run data available for re-processing.")
            return

        # Collect review PDFs
        review_pdfs = self._collect_review_pdfs()
        if not review_pdfs:
            messagebox.showinfo("No Files", "No files found that need review.")
            return

        result = messagebox.askyesno(
            "Re-run Flagged Files",
            f"Re-run processing on {len(review_pdfs)} files that were flagged for review?\n\n"
            "This will use any updated custom patterns."
        )

        if result:
            job_info = {
                "excel_path": self.last_run_info.get("result_path", ""),
                "input_path": review_pdfs,
                "is_rerun": True
            }
            self._start_worker_thread(job_info)

    def _start_worker_thread(self, job_info):
        """Start the background processing thread."""
        self.processing = True
        self.paused = False
        self.cancel_event.clear()
        self.pause_event.clear()
        self.start_time = time.time()
        
        # Reset counters
        self.count_pass.set(0)
        self.count_fail.set(0)
        self.count_review.set(0)
        self.count_ocr.set(0)
        self.progress_value.set(0)
        
        # Update UI state
        self._set_processing_ui_state(True)
        
        # Clear review tree
        for item in self.review_tree.get_children():
            self.review_tree.delete(item)
            
        # Start worker thread
        from processing_engine import run_processing_job
        self.worker_thread = threading.Thread(
            target=run_processing_job,
            args=(job_info, self.progress_queue, self.cancel_event, self.pause_event),
            daemon=True
        )
        self.worker_thread.start()
        
        log_info(self.logger, f"Started processing job: {job_info}")

    def _set_processing_ui_state(self, processing: bool):
        """Update UI elements based on processing state."""
        if processing:
            self.process_btn.config(state="disabled")
            self.pause_btn.config(state="normal")
            self.stop_btn.config(state="normal")
            self.rerun_btn.config(state="disabled")
            self.led_status_var.set("● Processing")
        else:
            self.process_btn.config(state="normal")
            self.pause_btn.config(state="disabled", text=" Pause", image=self.pause_icon)
            self.stop_btn.config(state="disabled")
            self.rerun_btn.config(state="normal")
            self.open_result_btn.config(state="normal" if self.result_file_path else "disabled")
            self.led_status_var.set("● Idle")

    # ------------------------------------------------------------------
    # Progress monitoring
    # ------------------------------------------------------------------
    def process_progress_queue(self):
        """Process messages from the progress queue."""
        try:
            while True:
                try:
                    message = self.progress_queue.get_nowait()
                    self._handle_progress_message(message)
                except Empty:
                    break
        except Exception as e:
            log_error(self.logger, f"Error processing progress queue: {e}")
        
        # Schedule next check
        self.after(100, self.process_progress_queue)

    def _handle_progress_message(self, message):
        """Handle individual progress messages."""
        msg_type = message.get("type")
        
        if msg_type == "log":
            self._add_log_message(message.get("tag", "info"), message.get("msg", ""))
        elif msg_type == "progress":
            self._update_progress(message.get("current", 0), message.get("total", 1))
        elif msg_type == "status":
            self.status_current_file.set(message.get("msg", ""))
            led_status = message.get("led")
            if led_status:
                self.led_status_var.set(f"● {led_status}")
        elif msg_type == "file_complete":
            self._handle_file_complete(message.get("status"))
        elif msg_type == "review_item":
            self._add_review_item(message.get("data"))
        elif msg_type == "increment_counter":
            self._increment_counter(message.get("counter"))
        elif msg_type == "result_path":
            self.result_file_path = message.get("path")
            self.open_result_btn.config(state="normal")
        elif msg_type == "finish":
            self._handle_processing_finished(message.get("status", "Complete"))

    def _add_log_message(self, tag: str, msg: str):
        """Add a message to the log display."""
        timestamp = time.strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {msg}\n"
        
        self.log_text.config(state="normal")
        self.log_text.insert("end", formatted_msg)
        
        # Apply color coding based on tag
        if tag == "error":
            self.log_text.tag_add("error", "end-2l", "end-1l")
            self.log_text.tag_config("error", foreground=BRAND_COLORS["fail_red"])
        elif tag == "warning":
            self.log_text.tag_add("warning", "end-2l", "end-1l")
            self.log_text.tag_config("warning", foreground=BRAND_COLORS["warning_orange"])
        elif tag == "success":
            self.log_text.tag_add("success", "end-2l", "end-1l")
            self.log_text.tag_config("success", foreground=BRAND_COLORS["success_green"])
        
        self.log_text.config(state="disabled")
        self.log_text.see("end")

    def _update_progress(self, current: int, total: int):
        """Update the progress bar and time estimate."""
        self.current_file_index = current
        self.total_files = total
        
        if total > 0:
            percentage = (current / total) * 100
            self.progress_value.set(percentage)
            
            # Calculate time remaining
            if self.start_time and current > 0:
                elapsed = time.time() - self.start_time
                rate = current / elapsed
                remaining_files = total - current
                if rate > 0:
                    remaining_seconds = remaining_files / rate
                    if remaining_seconds < 60:
                        self.time_remaining_var.set(f"{remaining_seconds:.0f}s remaining")
                    else:
                        minutes = remaining_seconds / 60
                        self.time_remaining_var.set(f"{minutes:.1f}m remaining")
                else:
                    self.time_remaining_var.set("")
            else:
                self.time_remaining_var.set("")

    def _handle_file_complete(self, status: str):
        """Handle completion of a single file."""
        if status == "Pass":
            self.count_pass.set(self.count_pass.get() + 1)
        elif status == "Fail":
            self.count_fail.set(self.count_fail.get() + 1)
        elif status == "Needs Review":
            self.count_review.set(self.count_review.get() + 1)

    def _add_review_item(self, data):
        """Add an item to the review tree."""
        if data:
            filename = data.get("filename", "Unknown")
            reason = data.get("reason", "Unknown")
            self.review_tree.insert("", "end", values=(f"{filename} - {reason}",), tags=(data,))

    def _increment_counter(self, counter: str):
        """Increment a specific counter."""
        if counter == "ocr":
            self.count_ocr.set(self.count_ocr.get() + 1)

    def _handle_processing_finished(self, status: str):
        """Handle completion of processing job."""
        self.processing = False
        self._set_processing_ui_state(False)
        
        self.status_current_file.set(f"Completed: {status}")
        self.time_remaining_var.set("")
        
        if status == "Complete":
            self.led_status_var.set("● Complete")
            log_info(self.logger, "Processing completed successfully")
            messagebox.showinfo("Processing Complete", "PDF processing completed successfully!")
        elif status == "Cancelled":
            self.led_status_var.set("● Cancelled")
            log_info(self.logger, "Processing was cancelled")
        else:
            self.led_status_var.set("● Error")
            log_error(self.logger, f"Processing failed: {status}")
            messagebox.showerror("Processing Failed", f"Processing failed: {status}")

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------
    def open_result(self) -> None:
        """Open the result Excel file."""
        if not self.result_file_path or not Path(self.result_file_path).exists():
            messagebox.showerror("File Not Found", "Result file not found or not yet generated.")
            return

        try:
            if sys.platform == "win32":
                os.startfile(self.result_file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.result_file_path])
            else:
                subprocess.run(["xdg-open", self.result_file_path])
            log_info(self.logger, f"Opened result file: {Path(self.result_file_path).name}")
        except Exception as e:
            log_error(self.logger, f"Failed to open result file: {e}")
            messagebox.showerror("Open Failed", f"Could not open result file: {e}")

    def open_review_folder(self) -> None:
        """Open the folder containing PDFs that need review."""
        try:
            review_path = NEED_REVIEW_DIR
            if not review_path.exists():
                review_path.mkdir(parents=True, exist_ok=True)
                
            if sys.platform == "win32":
                os.startfile(str(review_path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(review_path)])
            else:
                subprocess.run(["xdg-open", str(review_path)])
            log_info(self.logger, "Opened review folder")
        except Exception as e:
            log_error(self.logger, f"Failed to open review folder: {e}")
            messagebox.showinfo("Review Folder", f"Could not open folder automatically.\nPath: {review_path}")

    def open_pattern_manager(self) -> None:
        """Open the pattern management window."""
        try:
            ReviewWindow(self, "MODEL_PATTERNS", "Model Patterns")
        except Exception as e:
            log_error(self.logger, f"Failed to open pattern manager: {e}")
            messagebox.showerror("Error", f"Could not open pattern manager: {e}")

    def open_review_for_selected_file(self) -> None:
        """Open review window for the selected file in the review tree."""
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file from the review list.")
            return

        try:
            item = self.review_tree.item(selection[0])
            tags = item.get("tags")
            if tags:
                file_info = tags[0]  # The data is stored in the first tag
                ReviewWindow(self, "MODEL_PATTERNS", "Model Patterns", file_info)
        except Exception as e:
            log_error(self.logger, f"Failed to open review window: {e}")
            messagebox.showerror("Error", f"Could not open review window: {e}")

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        current_state = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not current_state)

    def on_closing(self) -> None:
        """Handle application closing."""
        if self.processing:
            if messagebox.askyesno("Processing Active", "Processing is still running. Stop and exit?"):
                self.cancel_event.set()
                if self.worker_thread and self.worker_thread.is_alive():
                    self.worker_thread.join(timeout=2)
                self.destroy()
        else:
            self.destroy()

    def _collect_review_pdfs(self) -> list[str]:
        """Return a list of PDF paths that require manual review."""
        if not self.last_run_info:
            return []

        input_base = Path(self.last_run_info.get("input_path", ""))
        needs_review_dir = PDF_TXT_DIR / "needs_review"
        if not needs_review_dir.exists():
            return []

        review_pdfs: list[str] = []
        for txt_file in needs_review_dir.glob("*.txt"):
            try:
                text = txt_file.read_text(encoding="utf-8")
            except Exception:
                continue

            if "Needs Review" not in text:
                continue

            pdf_name = None
            for line in text.splitlines():
                if line.startswith("File:"):
                    pdf_name = line.split(":", 1)[1].strip()
                    break
            if not pdf_name:
                continue

            candidate = input_base / pdf_name
            if candidate.exists():
                review_pdfs.append(str(candidate))
                continue

            for cache_json in CACHE_DIR.glob(f"{Path(pdf_name).stem}*.json"):
                try:
                    with open(cache_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "pdf_path" in data:
                        review_pdfs.append(data["pdf_path"])
                        break
                except Exception:
                    continue

        return review_pdfs


if __name__ == "__main__":
    app = KyoQAToolApp()
    app.mainloop()
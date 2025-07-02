# kyo_qa_tool_app.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import queue
import time
import sys

from config import BRAND_COLORS, ASSETS_DIR
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

# --- Class to redirect stdout/stderr to the UI ---
class TextRedirector(object):
    def __init__(self, widget_queue):
        self.widget_queue = widget_queue

    def write(self, s):
        self.widget_queue.put(s)

    def flush(self):
        pass

class KyoQAToolApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.terminal_queue = queue.Queue()
        sys.stdout = TextRedirector(self.terminal_queue)
        sys.stderr = TextRedirector(self.terminal_queue)

        self.count_pass = tk.IntVar(value=0)
        self.count_fail = tk.IntVar(value=0)
        self.count_review = tk.IntVar(value=0)
        self.count_ocr = tk.IntVar(value=0)
        self.count_needs_review = self.count_review

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
        self.is_fullscreen = True

        try:
            self.start_icon = tk.PhotoImage(file=ASSETS_DIR / "start.png")
            self.pause_icon = tk.PhotoImage(file=ASSETS_DIR / "pause.png")
            self.stop_icon = tk.PhotoImage(file=ASSETS_DIR / "stop.png")
            self.rerun_icon = tk.PhotoImage(file=ASSETS_DIR / "rerun.png")
            self.open_icon = tk.PhotoImage(file=ASSETS_DIR / "open.png")
            self.browse_icon = tk.PhotoImage(file=ASSETS_DIR / "browse.png")
            self.patterns_icon = tk.PhotoImage(file=ASSETS_DIR / "patterns.png")
            self.exit_icon = tk.PhotoImage(file=ASSETS_DIR / "exit.png")
        except tk.TclError:
            print("Warning: Icon files not found in 'assets' folder. Buttons will appear without icons.")
            self.start_icon = self.pause_icon = self.stop_icon = self.rerun_icon = self.open_icon = self.browse_icon = self.patterns_icon = self.exit_icon = None

        self.style = ttk.Style(self)
        self._setup_window_styles()
        self._create_widgets()

        ensure_folders()
        self.attributes("-fullscreen", self.is_fullscreen)
        self.bind("<Escape>", self.toggle_fullscreen)
        self.after(100, self.process_response_queue)
        self.after(100, self.process_terminal_queue)
        self.set_led("Ready")
        
        messagebox.showinfo(
            "Full-Screen Mode",
            "This application is now in full-screen mode.\n\nPress the ESC key at any time to enter or exit full-screen."
        )

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def _setup_window_styles(self):
        self.title(f"Kyocera QA Knowledge Tool v{VERSION}")
        self.geometry("1200x900")
        self.minsize(1000, 800)

        try:
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.configure(bg=BRAND_COLORS["background"])
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.style.theme_use("clam")
        self.style.configure("TFrame", background=BRAND_COLORS["background"])
        self.style.configure("Header.TFrame", background=BRAND_COLORS["frame_background"])
        self.style.configure("TLabel", background=BRAND_COLORS["background"], font=("Segoe UI", 10))
        self.style.configure("TLabelFrame", background=BRAND_COLORS["background"], borderwidth=1, relief="groove")
        self.style.configure("TLabelFrame.Label", background=BRAND_COLORS["background"], font=("Segoe UI", 11, "bold"))
        self.style.configure("Blue.Horizontal.TProgressbar", background=BRAND_COLORS["accent_blue"])
        self.style.configure("Treeview", font=("Segoe UI", 9), fieldbackground=BRAND_COLORS["frame_background"])
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[10, 5])

        self.style.configure("TEntry", fieldbackground=BRAND_COLORS["frame_background"], borderwidth=1, relief="solid")
        self.style.map("TEntry",
            bordercolor=[("focus", BRAND_COLORS["highlight_blue"]), ('!focus', 'grey')],
            lightcolor=[("focus", BRAND_COLORS["highlight_blue"])],
            darkcolor=[("focus", BRAND_COLORS["highlight_blue"])]
        )

        self.log_text_tags = {
            "info": ("#00529B", "white"), "warning": ("#9F6000", "#FEEFB3"),
            "error": ("#D8000C", "#FFD2D2"), "success": ("#4F8A10", "#DFF2BF")
        }

        self.style.configure("TButton", font=("Segoe UI", 10), padding=6, relief="raised")
        self.style.map("TButton", background=[('active', '#e0e0e0'), ('!active', '#f0f0f0')], foreground=[('active', 'black'), ('!active', 'black')])
        self.style.configure("Red.TButton", font=("Segoe UI", 12, "bold"), foreground="white")
        self.style.map("Red.TButton", background=[('active', '#A81F14'), ('!active', BRAND_COLORS["kyocera_red"])], foreground=[('active', 'white'), ('!active', 'white')])

        self.style.configure("Status.TFrame", background=BRAND_COLORS["status_default_bg"], relief="sunken", borderwidth=1)
        self.style.configure("Status.TLabel", font=("Segoe UI", 10))
        self.style.configure("Status.Header.TLabel", font=("Segoe UI", 10, "bold"))
        self.style.configure("LED.TLabel", font=("Segoe UI", 16))
        self.style.configure("Count.Green.TLabel", foreground=BRAND_COLORS["success_green"], font=("Segoe UI", 10, "bold"))
        self.style.configure("Count.Red.TLabel", foreground=BRAND_COLORS["fail_red"], font=("Segoe UI", 10, "bold"))
        self.style.configure("Count.Orange.TLabel", foreground=BRAND_COLORS["warning_orange"], font=("Segoe UI", 10, "bold"))
        self.style.configure("Count.Blue.TLabel", foreground=BRAND_COLORS["accent_blue"], font=("Segoe UI", 10, "bold"))

    def _create_widgets(self):
        create_main_header(self, VERSION, BRAND_COLORS)
        main_frame = ttk.Frame(self, padding=20)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        create_io_section(main_frame, self)
        create_process_controls(main_frame, self)
        create_status_and_log_section(main_frame, self)
        self.log_text.tag_configure("timestamp", foreground="grey")
        for tag, (fg, bg) in self.log_text_tags.items():
            self.log_text.tag_configure(f"{tag}_fg", foreground=fg)
            self.log_text.tag_configure(f"{tag}_line", background=bg, selectbackground=BRAND_COLORS["highlight_blue"])

    def process_terminal_queue(self):
        try:
            while not self.terminal_queue.empty():
                s = self.terminal_queue.get_nowait()
                self.terminal_text.config(state=tk.NORMAL)
                self.terminal_text.insert(tk.END, s)
                self.terminal_text.see(tk.END)
                self.terminal_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_terminal_queue)
    
    # --- FIX: Added a print() statement to send logs to the Live Terminal ---
    def log_message(self, message, level="info"):
        timestamp = time.strftime("%H:%M:%S")
        
        # This sends the log to the "Status & Logs" tab
        self.log_text.config(state=tk.NORMAL)
        start_index = self.log_text.index(tk.END)
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", f"{level}_fg")
        end_index = self.log_text.index(tk.END)
        if level in ["warning", "error", "success"]:
             self.log_text.tag_add(f"{level}_line", start_index, end_index)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        # This print() statement sends the same log to the "Live Terminal" tab
        print(f"[{timestamp}] [{level.upper()}] {message}")


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
        self.update_ui_for_start()
        self.log_message("Starting processing job...", "info")
        self.start_time = time.time()
        threading.Thread(target=run_processing_job, args=(job, self.response_queue, self.cancel_event, self.pause_event), daemon=True).start()

    def rerun_flagged_job(self):
        if not self.reviewable_files:
            messagebox.showwarning("No Files", "No files need re-running.")
            return
        if not self.result_file_path:
            messagebox.showerror("Error", "Previous result file not found.")
            return
        files = [item["pdf_path"] for item in self.reviewable_files]
        self.log_message(f"Re-running {len(files)} flagged files...", "info")
        self.start_processing(job={"excel_path": self.result_file_path, "input_path": files}, is_rerun=True)

    def browse_excel(self):
        path = filedialog.askopenfilename(title="Select Excel Template", filetypes=[("Excel Files", "*.xlsx *.xlsm"), ("All Files", "*.*")])
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
        paths = filedialog.askopenfilenames(title="Select PDF Files", filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")])
        if paths:
            self.selected_files_list = list(paths)
            self.selected_folder.set("")
            self.files_label.config(text=f"{len(paths)} files selected")
            self.log_message(f"{len(paths)} PDF files selected", "info")

    def toggle_pause(self):
        if not self.is_processing:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_event.set()
            self.pause_btn.config(text=" Resume")
        else:
            self.pause_event.clear()
            self.pause_btn.config(text=" Pause")
        self.log_message("Processing paused" if self.is_paused else "Processing resumed", "warning" if self.is_paused else "info")
        self.set_led("Paused" if self.is_paused else "Processing")

    def stop_processing(self):
        if not self.is_processing:
            return
        if messagebox.askyesno("Confirm Stop", "Stop the current processing job?"):
            self.cancel_event.set()
            self.log_message("Stopping processing...", "warning")
            self.set_led("Stopping")

    def on_closing(self):
        if self.is_processing and not messagebox.askyesno("Exit", "Processing is running. Exit anyway?"):
            return
        self.cancel_event.set()
        time.sleep(0.5)
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
        dialog = tk.Toplevel(self)
        dialog.title("Select Pattern Type")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        x = (self.winfo_screenwidth() // 2) - 150
        y = (self.winfo_screenheight() // 2) - 75
        dialog.geometry(f"+{x}+{y}")
        ttk.Label(dialog, text="Which patterns do you want to manage?", font=("Segoe UI", 10)).pack(pady=20)
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        def open_review(pattern_name, label):
            dialog.destroy()
            file_info = self.reviewable_files[0] if self.reviewable_files else None
            ReviewWindow(self, pattern_name, label, file_info)
        ttk.Button(button_frame, text="Model Patterns", command=lambda: open_review("MODEL_PATTERNS", "Model Patterns")).pack(side="left", padx=10)
        ttk.Button(button_frame, text="QA Patterns", command=lambda: open_review("QA_NUMBER_PATTERNS", "QA Number Patterns")).pack(side="left", padx=10)

    def set_led(self, status):
        led_config = {
            "Ready": ("#107C10", BRAND_COLORS["status_default_bg"]),
            "Processing": (BRAND_COLORS["accent_blue"], BRAND_COLORS["status_processing_bg"]),
            "OCR": (BRAND_COLORS["accent_blue"], BRAND_COLORS["status_ocr_bg"]),
            "AI": (BRAND_COLORS["accent_blue"], BRAND_COLORS["status_ai_bg"]),
            "Paused": (BRAND_COLORS["warning_orange"], BRAND_COLORS["status_default_bg"]),
            "Stopping": (BRAND_COLORS["fail_red"], BRAND_COLORS["status_default_bg"]),
            "Error": (BRAND_COLORS["fail_red"], BRAND_COLORS["status_default_bg"]),
            "Complete": ("#107C10", BRAND_COLORS["status_default_bg"]),
            "Queued": ("grey", BRAND_COLORS["status_default_bg"]),
            "Saving": ("#107C10", BRAND_COLORS["status_default_bg"]),
        }
        color, bg_color = led_config.get(status, ("grey", BRAND_COLORS["status_default_bg"]))
        self.led_label.config(foreground=color)
        self.status_frame.config(style="Status.TFrame")
        self.style.configure("Status.TFrame", background=bg_color)
        for child in self.status_frame.winfo_children():
            child.configure(style="Status.TLabel")
        self.style.configure("Status.TLabel", background=bg_color)

    def update_ui_for_start(self):
        self.is_processing = True
        self.is_paused = False
        self.cancel_event.clear()
        self.pause_event.clear()
        for var in [self.count_pass, self.count_fail, self.count_review, self.count_ocr]:
            var.set(0)
        self.reviewable_files.clear()
        self.review_tree.delete(*self.review_tree.get_children())
        self.process_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL, text=" Pause")
        self.stop_btn.config(state=tk.NORMAL)
        self.review_btn.config(state=tk.DISABLED)
        self.open_result_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.DISABLED)
        self.rerun_btn.config(state=tk.DISABLED)
        self.review_file_btn.config(state=tk.DISABLED)
        self.status_current_file.set("Initializing...")
        self.time_remaining_var.set("Calculating...")
        self.progress_value.set(0)
        self.set_led("Processing")

    def update_ui_for_finish(self, status):
        self.is_processing = False
        self.is_paused = False
        self.process_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text=" Pause")
        self.stop_btn.config(state=tk.DISABLED)
        self.exit_btn.config(state=tk.NORMAL)
        self.review_btn.config(state=tk.NORMAL)
        if self.result_file_path:
            self.open_result_btn.config(state=tk.NORMAL)
        if self.reviewable_files:
            self.rerun_btn.config(state=tk.NORMAL)
        final_status = "Complete" if status == "Complete" else "Error"
        self.status_current_file.set(f"Job {status}")
        self.time_remaining_var.set("Done!")
        self.set_led(final_status)
        self.progress_value.set(100)

    def open_review_for_selected_file(self):
        selection = self.review_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to review.")
            return
        item_id = selection[0]
        filename = self.review_tree.item(item_id, "values")[0]
        review_info = next((f for f in self.reviewable_files if f['filename'] == filename), None)
        if review_info:
            ReviewWindow(self, "MODEL_PATTERNS", "Model Patterns", review_info)
        else:
            messagebox.showerror("Error", "Could not find review information for the selected file.")

    def update_progress(self, current, total):
        if total > 0:
            percent = (current / total) * 100
            self.progress_value.set(percent)
            if self.start_time and current > 0:
                elapsed = time.time() - self.start_time
                rate = current / elapsed
                remaining = (total - current) / rate if rate > 0 else 0
                if remaining > 60:
                    self.time_remaining_var.set(f"~{int(remaining/60)}m {int(remaining%60)}s left")
                else:
                    self.time_remaining_var.set(f"~{int(remaining)}s left")

    def process_response_queue(self):
        try:
            while not self.response_queue.empty():
                msg = self.response_queue.get_nowait()
                mtype = msg.get("type")
                if mtype == "log":
                    # This now calls the updated log_message function
                    self.log_message(msg.get("msg", ""), msg.get("tag", "info"))
                elif mtype == "status":
                    self.status_current_file.set(msg.get("msg", ""))
                    if "led" in msg:
                        self.set_led(msg["led"])
                elif mtype == "progress":
                    self.update_progress(msg.get("current", 0), msg.get("total", 1))
                elif mtype == "increment_counter":
                    var = getattr(self, f"count_{msg.get('counter')}", None)
                    if var:
                        var.set(var.get() + 1)
                elif mtype == "file_complete":
                    var = getattr(self, f"count_{msg.get('status', '').lower().replace(' ', '_')}", None)
                    if var:
                        var.set(var.get() + 1)
                elif mtype == "review_item":
                    data = msg.get("data", {})
                    self.reviewable_files.append(data)
                    self.review_tree.insert('', 'end', values=(data.get('filename', 'Unknown'),))
                elif mtype == "result_path":
                    self.result_file_path = msg.get("path")
                elif mtype == "finish":
                    status = msg.get("status", "Complete")
                    elapsed = time.time() - self.start_time if self.start_time else 0
                    self.log_message(f"Job finished: {status} (Time: {int(elapsed/60)}m {int(elapsed%60)}s)", "success" if status == "Complete" else "error")
                    self.update_ui_for_finish(status)
        except queue.Empty:
            pass
        except Exception as e:
            self.log_message(f"Error processing queue: {e}", "error")
        self.after(100, self.process_response_queue)

if __name__ == "__main__":
    try:
        app = KyoQAToolApp()
        app.mainloop()
    except Exception as e:
        import traceback
        print(f"Failed to start application: {e}\n{traceback.format_exc()}")
        input("Press Enter to exit...")
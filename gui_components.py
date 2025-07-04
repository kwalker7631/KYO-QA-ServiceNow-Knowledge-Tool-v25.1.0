import tkinter as tk
from tkinter import ttk

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left', background="#ffffe0", relief='solid', borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

def create_main_header(parent, version, colors):
    """Creates the main header frame with title."""
    header_frame = ttk.Frame(parent, style="Header.TFrame", padding=(10, 5))
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
    header_frame.columnconfigure(0, weight=1)
    title_label = ttk.Label(header_frame, text=f"KYOCERA QA Knowledge Tool v{version}", style="Header.TLabel")
    title_label.grid(row=0, column=0, sticky="w")

def create_io_section(parent, app):
    """Creates the 'Select Inputs' frame."""
    io_frame = ttk.LabelFrame(parent, text="1. Select Inputs", padding=(10, 5))
    io_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
    io_frame.columnconfigure(1, weight=1)

    ttk.Label(io_frame, text="Excel to Clone:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    excel_entry = ttk.Entry(io_frame, textvariable=app.selected_excel)
    excel_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
    excel_browse_btn = ttk.Button(io_frame, text="Browse...", command=app.browse_excel)
    excel_browse_btn.grid(row=0, column=2, padx=5)
    ToolTip(excel_browse_btn, "Select the master Excel file to clone and update.")

    ttk.Label(io_frame, text="PDFs Folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    folder_entry = ttk.Entry(io_frame, textvariable=app.selected_folder)
    folder_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
    folder_browse_btn = ttk.Button(io_frame, text="Browse...", command=app.browse_folder)
    folder_browse_btn.grid(row=1, column=2, padx=5)
    ToolTip(folder_browse_btn, "Select a folder containing PDF files to process.")
    
    ttk.Label(io_frame, text="Or select individual files ->").grid(row=1, column=3, sticky="w", padx=10)
    files_btn = ttk.Button(io_frame, text="Browse Files...", command=app.browse_files)
    files_btn.grid(row=1, column=4, padx=5)
    ToolTip(files_btn, "Select one or more individual PDF files.")

def create_process_controls(parent, app):
    """Creates the 'Process & Manage' frame with all control buttons."""
    controls_frame = ttk.LabelFrame(parent, text="2. Process & Manage", padding=(10, 5))
    controls_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
    controls_frame.columnconfigure((0, 1, 2, 3), weight=1)

    app.start_btn = ttk.Button(controls_frame, text="START", command=app.start_processing, style="Accent.TButton")
    app.start_btn.grid(row=0, column=0, columnspan=4, sticky="ew", padx=5, pady=5)

    app.pause_btn = ttk.Button(controls_frame, text="Pause", command=app.toggle_pause, state=tk.DISABLED)
    app.pause_btn.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

    app.stop_btn = ttk.Button(controls_frame, text="Stop", command=app.stop_processing, state=tk.DISABLED)
    app.stop_btn.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

    app.rerun_btn = ttk.Button(controls_frame, text="Re-run Flagged", command=lambda: app.start_processing(is_rerun=True))
    app.rerun_btn.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
    ToolTip(app.rerun_btn, "Process only the files in the 'needs_review' folder.")

    app.open_result_btn = ttk.Button(controls_frame, text="Open Result", command=app.open_result_file, state=tk.DISABLED)
    app.open_result_btn.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
    ToolTip(app.open_result_btn, "Open the generated Excel report.")

    app.patterns_btn = ttk.Button(controls_frame, text="Patterns", command=app.open_review_tool)
    app.patterns_btn.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
    ToolTip(app.patterns_btn, "Modify the search patterns for data extraction.")

    app.fullscreen_btn = ttk.Button(controls_frame, text="Fullscreen", command=app.toggle_fullscreen)
    app.fullscreen_btn.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

    app.exit_btn = ttk.Button(controls_frame, text="Exit", command=app.on_closing)
    app.exit_btn.grid(row=2, column=3, sticky="ew", padx=5, pady=5)

def create_status_and_log_section(parent, app):
    """Creates the 'Status & Logs' frame."""
    status_frame = ttk.LabelFrame(parent, text="3. Status & Logs", padding=(10, 5))
    status_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
    status_frame.columnconfigure(0, weight=1)
    
    # Progress Bar
    app.progress_bar = ttk.Progressbar(status_frame, variable=app.progress_value, mode='determinate')
    app.progress_bar.grid(row=0, column=0, columnspan=5, sticky="ew", padx=5, pady=5)
    
    # Status Label
    ttk.Label(status_frame, text="●", foreground="green", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", padx=(5,0))
    app.status_label = ttk.Label(status_frame, textvariable=app.status_current_file)
    app.status_label.grid(row=1, column=1, sticky="w")
    
    # Counters
    counter_frame = ttk.Frame(status_frame)
    counter_frame.grid(row=1, column=4, sticky="e")
    ttk.Label(counter_frame, text="Pass:").pack(side="left", padx=(10, 2))
    ttk.Label(counter_frame, textvariable=app.pass_count).pack(side="left")
    ttk.Label(counter_frame, text="Fail:").pack(side="left", padx=(10, 2))
    ttk.Label(counter_frame, textvariable=app.fail_count).pack(side="left")
    ttk.Label(counter_frame, text="Review:").pack(side="left", padx=(10, 2))
    ttk.Label(counter_frame, textvariable=app.review_count).pack(side="left")
    ttk.Label(counter_frame, text="OCR:").pack(side="left", padx=(10, 2))
    ttk.Label(counter_frame, textvariable=app.ocr_count).pack(side="left")

def create_review_section(parent, app):
    """Creates the 'Files to Review' listbox."""
    review_frame = ttk.LabelFrame(parent, text="Files to Review", padding=(10, 5))
    review_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
    review_frame.columnconfigure(0, weight=1)
    review_frame.rowconfigure(0, weight=1)
    
    app.review_listbox = tk.Listbox(review_frame, listvariable=app.review_files, selectmode=tk.SINGLE)
    app.review_listbox.grid(row=0, column=0, sticky="nsew")
    
    scrollbar = ttk.Scrollbar(review_frame, orient="vertical", command=app.review_listbox.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    app.review_listbox.config(yscrollcommand=scrollbar.set)
    
    review_btn = ttk.Button(review_frame, text="Review Selected", command=app.review_selected_file)
    review_btn.grid(row=1, column=0, columnspan=2, sticky="e", pady=5)
    ToolTip(review_btn, "Open the selected file in the pattern editor.")

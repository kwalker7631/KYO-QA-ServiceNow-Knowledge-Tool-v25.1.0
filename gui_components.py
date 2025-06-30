# gui_components.py
import tkinter as tk
from tkinter import ttk

def create_main_header(parent, version, colors):
    """Creates the main header frame with the application title and logo."""
    header_frame = ttk.Frame(parent, style="Header.TFrame", padding=(10, 10))
    header_frame.grid(row=0, column=0, sticky="ew")
    separator = ttk.Separator(header_frame, orient='horizontal')
    separator.pack(side="bottom", fill="x")
    ttk.Label(header_frame, text="KYOCERA", foreground=colors["kyocera_red"], font=("Arial Black", 22)).pack(side=tk.LEFT, padx=(10, 0))
    ttk.Label(header_frame, text=f"QA Knowledge Tool v{version}", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, padx=(15, 0))
    return header_frame

def create_io_section(parent, app_instance):
    """Creates the frame for selecting input files and folders."""
    io_frame = ttk.LabelFrame(parent, text="1. Select Inputs", padding=10)
    io_frame.grid(row=0, column=0, sticky="ew", pady=5)
    io_frame.columnconfigure(1, weight=1)
    
    ttk.Label(io_frame, text="Excel File to Clone:").grid(row=0, column=0, sticky="w", pady=5, padx=5)
    ttk.Entry(io_frame, textvariable=app_instance.selected_excel).grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Button(io_frame, text="Browse...", command=app_instance.browse_excel).grid(row=0, column=2, padx=5)
    
    ttk.Label(io_frame, text="Process Folder:").grid(row=1, column=0, sticky="w", pady=5, padx=5)
    ttk.Entry(io_frame, textvariable=app_instance.selected_folder).grid(row=1, column=1, sticky="ew", padx=5)
    ttk.Button(io_frame, text="Browse...", command=app_instance.browse_folder).grid(row=1, column=2, padx=5)
    
    ttk.Label(io_frame, text="Or Select PDFs:").grid(row=2, column=0, sticky="w", pady=5, padx=5)
    app_instance.files_label = ttk.Label(io_frame, text="0 files selected")
    app_instance.files_label.grid(row=2, column=1, sticky="w", padx=5)
    ttk.Button(io_frame, text="Select...", command=app_instance.browse_files).grid(row=2, column=2, padx=5)
    return io_frame

def create_process_controls(parent, app_instance):
    """Creates the frame with all the main action buttons."""
    controls_frame = ttk.LabelFrame(parent, text="2. Process & Manage", padding=10)
    controls_frame.grid(row=1, column=0, sticky="ew", pady=5)
    controls_frame.columnconfigure(0, weight=1)
    controls_frame.columnconfigure(1, weight=1)
    
    app_instance.process_btn = ttk.Button(controls_frame, text="▶ START PROCESSING", command=app_instance.start_processing, style="Red.TButton", padding=(10,8))
    app_instance.process_btn.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
    
    app_instance.pause_btn = ttk.Button(controls_frame, text="⏯️ Pause", command=app_instance.toggle_pause, state=tk.DISABLED)
    app_instance.pause_btn.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
    app_instance.stop_btn = ttk.Button(controls_frame, text="⏹️ Stop", command=app_instance.stop_processing, state=tk.DISABLED)
    app_instance.stop_btn.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    app_instance.rerun_btn = ttk.Button(controls_frame, text="🔄 Re-run Flagged", command=app_instance.rerun_flagged_job, state=tk.DISABLED)
    app_instance.rerun_btn.grid(row=1, column=2, padx=5, pady=5, sticky="ew")
    app_instance.open_result_btn = ttk.Button(controls_frame, text="📂 Open Result", command=app_instance.open_result, state=tk.DISABLED)
    app_instance.open_result_btn.grid(row=1, column=3, padx=5, pady=5, sticky="ew")
    
    app_instance.review_btn = ttk.Button(controls_frame, text="⚙️ Pattern Manager", command=app_instance.open_pattern_manager)
    app_instance.review_btn.grid(row=2, column=0, padx=5, pady=5, sticky="ew")
    app_instance.exit_btn = ttk.Button(controls_frame, text="❌ Exit", command=app_instance.on_closing)
    app_instance.exit_btn.grid(row=2, column=3, padx=5, pady=5, sticky="ew")
    return controls_frame

def create_status_and_log_section(parent, app_instance):
    """Creates the bottom section with status, logs, and review list."""
    container = ttk.LabelFrame(parent, text="3. Live Status & Activity Log", padding=10)
    container.grid(row=2, column=0, sticky="nsew", pady=5)
    container.columnconfigure(0, weight=1)
    container.rowconfigure(3, weight=1)
    
    # Status Frame
    status_frame = ttk.Frame(container, style="Dark.TFrame", padding=10)
    status_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    status_frame.columnconfigure(2, weight=1)
    ttk.Label(status_frame, text="Current File:", style="Status.Header.TLabel").grid(row=0, column=0, sticky="w", padx=5)
    app_instance.led_label = ttk.Label(status_frame, textvariable=app_instance.led_status_var, style="LED.TLabel", anchor="w")
    app_instance.led_label.grid(row=0, column=1, sticky="w", padx=5)
    ttk.Label(status_frame, textvariable=app_instance.status_current_file, style="Status.TLabel", anchor="w").grid(row=0, column=2, sticky="ew", padx=5)
    ttk.Label(status_frame, text="Overall Progress:", style="Status.Header.TLabel").grid(row=1, column=0, sticky="w", padx=5)
    app_instance.progress_bar = ttk.Progressbar(status_frame, orient='horizontal', mode='determinate', variable=app_instance.progress_value, style="Blue.Horizontal.TProgressbar")
    app_instance.progress_bar.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=(10,5))
    ttk.Label(status_frame, textvariable=app_instance.time_remaining_var, style="Status.TLabel", anchor="e").grid(row=1, column=3, sticky="e", padx=10)

    # Summary Frame
    summary_frame = ttk.Frame(container, style="Dark.TFrame", padding=10)
    summary_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(5,0))
    summary_frame.columnconfigure(1, weight=1)
    summary_frame.columnconfigure(3, weight=1)
    summary_frame.columnconfigure(5, weight=1)
    summary_frame.columnconfigure(7, weight=1)
    
    # Create summary labels
    ttk.Label(summary_frame, text="✅ Pass:", style="Status.Header.TLabel").grid(row=0, column=0, sticky="w", padx=5)
    ttk.Label(summary_frame, textvariable=app_instance.count_pass, style="Status.Count.TLabel").grid(row=0, column=1, sticky="w", padx=5)
    ttk.Label(summary_frame, text="❌ Fail:", style="Status.Header.TLabel").grid(row=0, column=2, sticky="w", padx=5)
    ttk.Label(summary_frame, textvariable=app_instance.count_fail, style="Status.Count.TLabel").grid(row=0, column=3, sticky="w", padx=5)
    ttk.Label(summary_frame, text="🔍 Review:", style="Status.Header.TLabel").grid(row=0, column=4, sticky="w", padx=5)
    ttk.Label(summary_frame, textvariable=app_instance.count_review, style="Status.Count.TLabel").grid(row=0, column=5, sticky="w", padx=5)
    ttk.Label(summary_frame, text="📷 OCR:", style="Status.Header.TLabel").grid(row=0, column=6, sticky="w", padx=5)
    ttk.Label(summary_frame, textvariable=app_instance.count_ocr, style="Status.Count.TLabel").grid(row=0, column=7, sticky="w", padx=5)
    
    # Review Frame
    review_frame = ttk.Frame(container, style="Dark.TFrame", padding=(5, 10))
    review_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=(5,0))
    review_frame.columnconfigure(0, weight=1)
    
    review_label = ttk.Label(review_frame, text="📋 Files Needing Review:", style="Status.Header.TLabel")
    review_label.grid(row=0, column=0, sticky="w", padx=5)
    
    # Create review listbox with scrollbar
    review_list_frame = ttk.Frame(review_frame)
    review_list_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
    review_list_frame.columnconfigure(0, weight=1)
    
    app_instance.review_listbox = tk.Listbox(review_list_frame, height=3, font=("Consolas", 9))
    app_instance.review_listbox.grid(row=0, column=0, sticky="ew")
    
    review_scrollbar = ttk.Scrollbar(review_list_frame, orient="vertical", command=app_instance.review_listbox.yview)
    review_scrollbar.grid(row=0, column=1, sticky="ns")
    app_instance.review_listbox.config(yscrollcommand=review_scrollbar.set)

    # Log Frame
    log_text_frame = ttk.Frame(container)
    log_text_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
    log_text_frame.columnconfigure(0, weight=1)
    log_text_frame.rowconfigure(0, weight=1)
    
    # Create log text widget with scrollbar
    app_instance.log_text = tk.Text(log_text_frame, wrap="word", height=10, font=("Consolas", 9))
    app_instance.log_text.grid(row=0, column=0, sticky="nsew")
    
    log_scrollbar = ttk.Scrollbar(log_text_frame, orient="vertical", command=app_instance.log_text.yview)
    log_scrollbar.grid(row=0, column=1, sticky="ns")
    app_instance.log_text.config(yscrollcommand=log_scrollbar.set)
    
    # Configure log text tags for colored output
    app_instance.log_text.tag_config("info", foreground="black")
    app_instance.log_text.tag_config("success", foreground="green")
    app_instance.log_text.tag_config("warning", foreground="orange")
    app_instance.log_text.tag_config("error", foreground="red")
    
    return container
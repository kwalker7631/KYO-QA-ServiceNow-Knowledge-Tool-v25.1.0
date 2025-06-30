# gui_components.py
import tkinter as tk
from tkinter import ttk

def create_main_header(parent, version, colors):
    header = ttk.Frame(parent, style="Header.TFrame", padding=(10, 10))
    header.grid(row=0, column=0, sticky="ew")
    ttk.Separator(header, orient='horizontal').pack(side="bottom", fill="x")
    ttk.Label(header, text="KYOCERA", foreground=colors["kyocera_red"], font=("Arial Black", 22)).pack(side=tk.LEFT, padx=(10, 0))
    ttk.Label(header, text=f"QA Knowledge Tool v{version}", font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, padx=(15, 0))

def create_io_section(parent, app):
    io = ttk.LabelFrame(parent, text="1. Select Inputs", padding=10)
    io.grid(row=0, column=0, sticky="ew", pady=5); io.columnconfigure(1, weight=1)

    ttk.Label(io, text="Excel to Clone:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
    ttk.Entry(io, textvariable=app.selected_excel).grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Button(io, text="Browse...", command=app.browse_excel).grid(row=0, column=2, padx=5)

    ttk.Label(io, text="PDFs Folder:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
    ttk.Entry(io, textvariable=app.selected_folder).grid(row=1, column=1, sticky="ew", padx=5)
    ttk.Button(io, text="Browse...", command=app.browse_folder).grid(row=1, column=2, padx=5)

    app.files_label = ttk.Label(io, text="Or select individual files -->")
    app.files_label.grid(row=2, column=1, sticky="e", padx=5, pady=(5,0))
    ttk.Button(io, text="Browse Files...", command=app.browse_files).grid(row=2, column=2, padx=5, pady=(5,0))

def create_process_controls(parent, app):
    ctrl = ttk.LabelFrame(parent, text="2. Process & Manage", padding=10)
    ctrl.grid(row=1, column=0, sticky="ew", pady=5); ctrl.columnconfigure(0, weight=1)
    app.process_btn = ttk.Button(ctrl, text="▶ START", command=app.start_processing, style="Red.TButton"); app.process_btn.grid(row=0, column=0, columnspan=4, sticky="ew", pady=2)
    app.pause_btn = ttk.Button(ctrl, text="⏯️ Pause", command=app.toggle_pause, state=tk.DISABLED); app.pause_btn.grid(row=1, column=0, sticky="ew", pady=2)
    app.stop_btn = ttk.Button(ctrl, text="⏹️ Stop", command=app.stop_processing, state=tk.DISABLED); app.stop_btn.grid(row=1, column=1, sticky="ew", pady=2)
    app.rerun_btn = ttk.Button(ctrl, text="🔄 Re-run Flagged", command=app.rerun_flagged_job, state=tk.DISABLED); app.rerun_btn.grid(row=1, column=2, sticky="ew", padx=5, pady=2)
    app.open_result_btn = ttk.Button(ctrl, text="📂 Open Result", command=app.open_result, state=tk.DISABLED); app.open_result_btn.grid(row=1, column=3, sticky="ew", pady=2)
    app.review_btn = ttk.Button(ctrl, text="⚙️ Patterns", command=app.open_pattern_manager); app.review_btn.grid(row=2, column=0, sticky="ew", pady=2)
    app.exit_btn = ttk.Button(ctrl, text="❌ Exit", command=app.on_closing); app.exit_btn.grid(row=2, column=3, sticky="ew", pady=2)

def create_status_and_log_section(parent, app):
    stat = ttk.LabelFrame(parent, text="3. Status & Logs", padding=10)
    stat.grid(row=2, column=0, sticky="nsew", pady=5); stat.columnconfigure(0, weight=1); stat.rowconfigure(3, weight=1)
    s_frame = ttk.Frame(stat); s_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2); s_frame.columnconfigure(2, weight=1)
    ttk.Label(s_frame, text="File:", style="Status.Header.TLabel").grid(row=0, column=0, sticky="w"); app.led_label = ttk.Label(s_frame, textvariable=app.led_status_var); app.led_label.grid(row=0, column=1, sticky="w", padx=5); ttk.Label(s_frame, textvariable=app.status_current_file).grid(row=0, column=2, sticky="ew")
    ttk.Label(s_frame, text="Progress:", style="Status.Header.TLabel").grid(row=1, column=0, sticky="w"); app.progress_bar = ttk.Progressbar(s_frame, variable=app.progress_value, style="Blue.Horizontal.TProgressbar"); app.progress_bar.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5); ttk.Label(s_frame, textvariable=app.time_remaining_var).grid(row=1, column=3, sticky="e", padx=10)
    sum_frame = ttk.Frame(stat); sum_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
    for i, (text, var) in enumerate([("Pass:", app.count_pass), ("Fail:", app.count_fail), ("Review:", app.count_review), ("OCR:", app.count_ocr)]):
        ttk.Label(sum_frame, text=text, style="Status.Header.TLabel").pack(side="left", padx=(10,2)); ttk.Label(sum_frame, textvariable=var).pack(side="left", padx=(0,10))
    rev_frame = ttk.Frame(stat); rev_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=2); rev_frame.columnconfigure(0, weight=1)
    ttk.Label(rev_frame, text="Files to Review:", style="Status.Header.TLabel").pack(side="left")
    app.review_file_btn = ttk.Button(rev_frame, text="Review Selected", command=app.open_review_for_selected_file, state=tk.DISABLED); app.review_file_btn.pack(side="right")
    app.review_tree = ttk.Treeview(rev_frame, columns=('file'), show='headings', height=3); app.review_tree.pack(fill="x", expand=True, pady=2); app.review_tree.heading('file', text='File Name'); app.review_tree.bind("<<TreeviewSelect>>", lambda e: app.review_file_btn.config(state=tk.NORMAL))
    log_frame = ttk.Frame(stat); log_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=2); log_frame.rowconfigure(0, weight=1); log_frame.columnconfigure(0, weight=1)
    app.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, state=tk.DISABLED); app.log_text.grid(row=0, column=0, sticky="nsew")
    log_scroll = ttk.Scrollbar(log_frame, command=app.log_text.yview); log_scroll.grid(row=0, column=1, sticky="ns"); app.log_text.config(yscrollcommand=log_scroll.set)
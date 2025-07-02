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
    io.grid(row=0, column=0, sticky="ew", pady=5)
    io.columnconfigure(1, weight=1)

    ttk.Label(io, text="Excel to Clone:").grid(row=0, column=0, sticky="w", pady=2, padx=5)
    ttk.Entry(io, textvariable=app.selected_excel).grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Button(io, image=app.browse_icon, text=" Browse...", compound="left", command=app.browse_excel).grid(row=0, column=2, padx=5)

    ttk.Label(io, text="PDFs Folder:").grid(row=1, column=0, sticky="w", pady=2, padx=5)
    ttk.Entry(io, textvariable=app.selected_folder).grid(row=1, column=1, sticky="ew", padx=5)
    ttk.Button(io, image=app.browse_icon, text=" Browse...", compound="left", command=app.browse_folder).grid(row=1, column=2, padx=5)

    app.files_label = ttk.Label(io, text="Or select individual files -->")
    app.files_label.grid(row=2, column=1, sticky="e", padx=5, pady=(5,0))
    ttk.Button(io, image=app.browse_icon, text=" Browse Files...", compound="left", command=app.browse_files).grid(row=2, column=2, padx=5, pady=(5,0))

def create_process_controls(parent, app):
    ctrl = ttk.LabelFrame(parent, text="2. Process & Manage", padding=10)
    ctrl.grid(row=1, column=0, sticky="ew", pady=5)
    ctrl.columnconfigure(0, weight=1)

    app.process_btn = ttk.Button(ctrl, text=" START", image=app.start_icon, compound="left", command=app.start_processing, style="Red.TButton")
    app.process_btn.grid(row=0, column=0, columnspan=4, sticky="ew", pady=2)

    app.pause_btn = ttk.Button(ctrl, text=" Pause", image=app.pause_icon, compound="left", command=app.toggle_pause, state=tk.DISABLED)
    app.pause_btn.grid(row=1, column=0, sticky="ew", pady=2)
    app.stop_btn = ttk.Button(ctrl, text=" Stop", image=app.stop_icon, compound="left", command=app.stop_processing, state=tk.DISABLED)
    app.stop_btn.grid(row=1, column=1, sticky="ew", pady=2)
    app.rerun_btn = ttk.Button(ctrl, text=" Re-run Flagged", image=app.rerun_icon, compound="left", command=app.rerun_flagged_job, state=tk.DISABLED)
    app.rerun_btn.grid(row=1, column=2, sticky="ew", padx=5, pady=2)
    app.open_result_btn = ttk.Button(ctrl, text=" Open Result", image=app.open_icon, compound="left", command=app.open_result, state=tk.DISABLED)
    app.open_result_btn.grid(row=1, column=3, sticky="ew", pady=2)
    
    # --- FIX: Restored the missing 'Patterns' and 'Exit' buttons ---
    app.review_btn = ttk.Button(ctrl, text=" Patterns", image=app.patterns_icon, compound="left", command=app.open_pattern_manager)
    app.review_btn.grid(row=2, column=0, sticky="ew", pady=2)
    app.retry_ocr_btn = ttk.Button(
        ctrl,
        text=" Retry OCR",
        image=app.rerun_icon,
        compound="left",
        command=app.retry_failed_ocr,
        state=tk.DISABLED,
    )
    app.retry_ocr_btn.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
    app.exit_btn = ttk.Button(ctrl, text=" Exit", image=app.exit_icon, compound="left", command=app.on_closing)
    app.exit_btn.grid(row=2, column=3, sticky="ew", pady=2)

def create_status_and_log_section(parent, app):
    notebook = ttk.Notebook(parent)
    notebook.grid(row=2, column=0, sticky="nsew", pady=5)
    parent.rowconfigure(2, weight=1)

    status_tab = ttk.Frame(notebook, padding=10)
    notebook.add(status_tab, text="Status & Logs")
    status_tab.columnconfigure(0, weight=1)
    status_tab.rowconfigure(5, weight=1)

    app.status_frame = ttk.Frame(status_tab, style="Status.TFrame", padding=5)
    app.status_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
    app.status_frame.columnconfigure(1, weight=1)
    app.led_label = ttk.Label(app.status_frame, textvariable=app.led_status_var, style="LED.TLabel")
    app.led_label.grid(row=0, column=0, sticky="w")
    ttk.Label(app.status_frame, textvariable=app.status_current_file, style="Status.TLabel").grid(row=0, column=1, sticky="ew", padx=5)

    prog_frame = ttk.Frame(status_tab)
    prog_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(5,10))
    prog_frame.columnconfigure(0, weight=1)
    app.progress_bar = ttk.Progressbar(prog_frame, variable=app.progress_value, style="Blue.Horizontal.TProgressbar")
    app.progress_bar.grid(row=0, column=0, sticky="ew")
    ttk.Label(prog_frame, textvariable=app.progress_percent_var).grid(row=0, column=1, sticky="w", padx=5)
    ttk.Label(prog_frame, textvariable=app.time_remaining_var).grid(row=0, column=2, sticky="e", padx=10)
    app.cancel_progress_btn = ttk.Button(prog_frame, text="Cancel", command=app.stop_processing, state=tk.DISABLED)
    app.cancel_progress_btn.grid(row=0, column=3, padx=(10,0))
    ttk.Label(status_tab, textvariable=app.stage_var).grid(row=2, column=0, sticky="w", padx=5)

    sum_frame = ttk.Frame(status_tab)
    sum_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=2)
    counters = [("Pass:", app.count_pass, "Green"), ("Fail:", app.count_fail, "Red"), ("Review:", app.count_review, "Orange"), ("OCR:", app.count_ocr, "Blue")]
    for i, (text, var, color) in enumerate(counters):
        ttk.Label(sum_frame, text=text, style="Status.Header.TLabel").pack(side="left", padx=(15, 2))
        ttk.Label(sum_frame, textvariable=var, style=f"Count.{color}.TLabel").pack(side="left")

    rev_frame = ttk.Frame(status_tab)
    rev_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=2)
    rev_frame.rowconfigure(1, weight=1)
    rev_frame.columnconfigure(0, weight=1)
    ttk.Label(rev_frame, text="Files to Review:", style="Status.Header.TLabel").grid(row=0, column=0, sticky="w")
    app.review_file_btn = ttk.Button(rev_frame, text="Review Selected", command=app.open_review_for_selected_file, state=tk.DISABLED)
    app.review_file_btn.grid(row=0, column=1, sticky="e")
    app.review_tree = ttk.Treeview(rev_frame, columns=('file'), show='headings', height=4)
    app.review_tree.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=2)
    app.review_tree.heading('file', text='File Name')
    app.review_tree.bind("<<TreeviewSelect>>", lambda e: app.review_file_btn.config(state=tk.NORMAL))

    log_frame = ttk.Frame(status_tab)
    log_frame.grid(row=5, column=0, sticky="nsew", padx=5, pady=(10,2))
    log_frame.rowconfigure(0, weight=1)
    log_frame.columnconfigure(0, weight=1)
    app.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, state=tk.DISABLED, relief="solid", borderwidth=1, font=("Consolas", 9))
    app.log_text.grid(row=0, column=0, sticky="nsew")
    log_scroll = ttk.Scrollbar(log_frame, command=app.log_text.yview)
    log_scroll.grid(row=0, column=1, sticky="ns")
    app.log_text.config(yscrollcommand=log_scroll.set)
    
    terminal_tab = ttk.Frame(notebook, padding=10)
    notebook.add(terminal_tab, text="Live Terminal")
    terminal_tab.rowconfigure(0, weight=1)
    terminal_tab.columnconfigure(0, weight=1)
    
    app.terminal_text = tk.Text(terminal_tab, wrap=tk.WORD, state=tk.DISABLED, background="black", foreground="#E0E0E0", font=("Consolas", 10), insertbackground="white")
    app.terminal_text.grid(row=0, column=0, sticky="nsew")
    term_scroll = ttk.Scrollbar(terminal_tab, command=app.terminal_text.yview)
    term_scroll.grid(row=0, column=1, sticky="ns")
    app.terminal_text.config(yscrollcommand=term_scroll.set)
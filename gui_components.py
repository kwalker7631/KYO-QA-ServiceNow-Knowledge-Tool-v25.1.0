# gui_components.py
import tkinter as tk
from tkinter import ttk, font, filedialog
try:
    from branding import KyoceraColors
except ImportError:
    class KyoceraColors:
        DARK_GREY, PURPLE = "#282828", "#6D2C91"
        LIGHT_GREY = "#F2F2F2"
        STATUS_ORANGE_LIGHT, STATUS_BLUE_LIGHT, STATUS_GREEN_LIGHT, STATUS_RED_LIGHT = \
            "#FAD9C6", "#CCE5F3", "#CCEFDA", "#F5B7B1"

def setup_styles():
    style = ttk.Style()
    if "clam" not in style.theme_names(): return
    style.theme_use('clam')
    style.configure('.', background=KyoceraColors.LIGHT_GREY, foreground=KyoceraColors.DARK_GREY, font=('Helvetica', 10))
    style.configure('TFrame', background=KyoceraColors.LIGHT_GREY)
    style.configure('TLabel', background=KyoceraColors.LIGHT_GREY, foreground=KyoceraColors.DARK_GREY)
    style.configure('Header.TFrame', background=KyoceraColors.DARK_GREY)
    style.configure('Header.TLabel', background=KyoceraColors.DARK_GREY, foreground='white', font=('Helvetica', 16, 'bold'))
    style.configure('TButton', background=KyoceraColors.DARK_GREY, foreground='white', font=('Helvetica', 10, 'bold'), padding=5)
    style.map('TButton', background=[('active', KyoceraColors.PURPLE)])
    style.configure('Run.TButton', background=KyoceraColors.PURPLE, font=('Helvetica', 11, 'bold'))
    style.map('Run.TButton', background=[('active', KyoceraColors.DARK_GREY)])

def create_main_header(parent, version, colors):
    header_frame = ttk.Frame(parent, style='Header.TFrame', height=50)
    header_frame.pack(fill="x", side="top", ipady=5)
    title_text = f"KYOCERA ServiceNow Knowledge Tool {version}"
    header_label = ttk.Label(header_frame, text=title_text, style='Header.TLabel')
    header_label.pack()
    return header_frame

def create_io_section(parent, app):
    io_frame = ttk.Frame(parent, padding="10 10 10 5")
    io_frame.pack(fill="x")
    io_frame.columnconfigure(1, weight=1)
    input_path, output_path = tk.StringVar(), tk.StringVar()
    def _browse_input():
        path = filedialog.askopenfilename(title='Select Input File', filetypes=(('Excel files', '*.xlsx'), ('PDF files', '*.pdf'), ('All files', '*.*')))
        if path: input_path.set(path)
    def _browse_output():
        path = filedialog.askdirectory(title='Select Output Folder')
        if path: output_path.set(path)
    ttk.Label(io_frame, text="Input File:").grid(row=0, column=0, sticky="w", padx=(0, 10))
    ttk.Entry(io_frame, textvariable=input_path, state="readonly").grid(row=0, column=1, sticky="ew")
    ttk.Button(io_frame, text="Browse...", command=_browse_input).grid(row=0, column=2, sticky="e", padx=(5, 0))
    ttk.Label(io_frame, text="Output Folder:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
    ttk.Entry(io_frame, textvariable=output_path, state="readonly").grid(row=1, column=1, sticky="ew", pady=(5, 0))
    ttk.Button(io_frame, text="Browse...", command=_browse_output).grid(row=1, column=2, sticky="e", padx=(5, 0), pady=(5, 0))
    app.input_path, app.output_path = input_path, output_path
    return input_path, output_path

def create_process_controls(parent, run_callback):
    control_frame = ttk.Frame(parent, padding="5 10")
    control_frame.pack(fill="x")
    run_button = ttk.Button(control_frame, text="Run QA Check", command=run_callback, style='Run.TButton')
    run_button.pack(pady=5)
    return run_button

def create_status_and_log_section(parent, app):
    frame = ttk.Frame(parent, padding="10 0 10 10")
    frame.pack(fill="both", expand=True)
    log_text = tk.Text(frame, wrap="word", font=("Helvetica", 10), bg=KyoceraColors.LIGHT_GREY, fg=KyoceraColors.DARK_GREY, relief="solid", borderwidth=1, padx=10, pady=10)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=log_text.yview)
    log_text.config(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    log_text.pack(side="left", fill="both", expand=True)
    log_text.tag_configure("center", justify='center')
    log_text.tag_configure("header", justify='center', font=("Helvetica", 14, "bold"))
    log_text.insert("1.0", "Welcome to the KYO QA Knowledge Tool\n\n", "header")
    log_text.insert(tk.END, "1. Select an 'Input File' to be checked.\n2. Select an 'Output Folder' to save the results.\n3. Click 'Run QA Check' to begin.\n\nResults will be displayed here.", "center")
    log_text.config(state="disabled")
    log_text.tag_configure("error", background=KyoceraColors.STATUS_RED_LIGHT, foreground=KyoceraColors.DARK_GREY)
    log_text.tag_configure("warning", background=KyoceraColors.STATUS_ORANGE_LIGHT, foreground=KyoceraColors.DARK_GREY)
    log_text.tag_configure("info", foreground=KyoceraColors.DARK_GREY)
    log_text.tag_configure("success", foreground=KyoceraColors.PURPLE)
    return log_text

def create_status_bar(parent):
    status_bar = tk.Label(parent, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W, bg=KyoceraColors.DARK_GREY, fg='white', font=('Helvetica', 9))
    status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    return status_bar
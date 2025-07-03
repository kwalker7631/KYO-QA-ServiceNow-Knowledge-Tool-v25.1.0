# repair_my_app.py
# A master script to restore all core application files to a known, working state.
# This version includes restored processing logic and real-time feedback.

import os
import logging

# Set up basic logging for this script
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ==============================================================================
#  BEGIN DEFINITION OF ALL CORRECT FILE CONTENTS
# ==============================================================================

CORRECT_FILES = {

    # --- file_utils.py ---
    "file_utils.py": """
# file_utils.py
import os

def get_file_extension(filename):
    \"\"\"Returns the file extension in lowercase, e.g., '.pdf'.\"\"\"
    if not filename or not isinstance(filename, str):
        return ""
    return os.path.splitext(filename)[1].lower()
""",

    # --- branding.py ---
    "branding.py": """
# branding.py
class KyoceraColors:
    DARK_GREY, PURPLE = "#282828", "#6D2C91"
    LIGHT_GREY = "#F2F2F2"
    STATUS_ORANGE_LIGHT, STATUS_BLUE_LIGHT, STATUS_GREEN_LIGHT, STATUS_RED_LIGHT = \\
        "#FAD9C6", "#CCE5F3", "#CCEFDA", "#F5B7B1"
""",

    # --- gui_components.py ---
    "gui_components.py": """
# gui_components.py
import tkinter as tk
from tkinter import ttk, font, filedialog
try:
    from branding import KyoceraColors
except ImportError:
    class KyoceraColors:
        DARK_GREY, PURPLE = "#282828", "#6D2C91"
        LIGHT_GREY = "#F2F2F2"
        STATUS_ORANGE_LIGHT, STATUS_BLUE_LIGHT, STATUS_GREEN_LIGHT, STATUS_RED_LIGHT = \\
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
    log_text.insert("1.0", "Welcome to the KYO QA Knowledge Tool\\n\\n", "header")
    log_text.insert(tk.END, "1. Select an 'Input File' to be checked.\\n2. Select an 'Output Folder' to save the results.\\n3. Click 'Run QA Check' to begin.\\n\\nResults will be displayed here.", "center")
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
""",

    # --- excel_generator.py ---
    "excel_generator.py": """
# excel_generator.py
import logging
import pandas as pd
logger = logging.getLogger(__name__)
class ExcelGenerator:
    def __init__(self, output_filepath):
        self.output_filepath = output_filepath
    def create_report(self, data):
        if not data:
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data)
        try:
            with pd.ExcelWriter(self.output_filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='QA_Report', index=False)
        except Exception as e:
            logger.error(f"Failed to create Excel report: {e}")
            raise
""",

    # --- data_harvesters.py ---
    "data_harvesters.py": """
# data_harvesters.py
import logging
import pandas as pd
logger = logging.getLogger(__name__)
KNOWLEDGE_BASE_FIELDS = ['number', 'short_description', 'kb_knowledge_base']
class DataHarvester:
    def harvest_from_excel(self, file_path):
        try:
            # More adaptable: Try to find a relevant sheet name
            xls = pd.ExcelFile(file_path)
            sheet_name_to_use = 'Page 1' # Default
            for name in xls.sheet_names:
                if 'knowledge' in name.lower() or 'kb' in name.lower():
                    sheet_name_to_use = name
                    break
            df = pd.read_excel(xls, sheet_name=sheet_name_to_use)
            # Standardize column names (e.g., 'Number' -> 'number')
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Failed to harvest data from Excel file '{file_path}': {e}")
            return []
    def harvest_from_text(self, text_content):
        if text_content:
            return [{'number': 'TXT_001', 'short_description': 'Content from PDF', 'article_body': text_content[:500] + '...'}]
        return []
""",

    # --- ocr_utils.py ---
    "ocr_utils.py": """
# ocr_utils.py
import fitz
from PIL import Image
def _is_ocr_needed(page):
    return len(page.get_text("text").strip()) < 100
def extract_text_from_pdf(pdf_path):
    full_text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                if _is_ocr_needed(page):
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    # Placeholder for actual OCR logic
                    full_text += f"[OCR Content from Page {page.number + 1}]\\n"
                else:
                    full_text += page.get_text() + "\\n"
    except Exception as e:
        return f"Error reading PDF: {e}"
    return correct_ocr_errors(text)
def correct_ocr_errors(text):
    corrections = {"Waming": "Warning", "lnc.": "Inc.", "Err0r": "Error"}
    for wrong, right in corrections.items():
        text = text.replace(wrong, right)
    return text
""",

    # --- processing_engine.py ---
    "processing_engine.py": """
# processing_engine.py
import logging
from pathlib import Path
import pandas as pd
from data_harvesters import DataHarvester
from excel_generator import ExcelGenerator
from ocr_utils import extract_text_from_pdf
from file_utils import get_file_extension
logger = logging.getLogger(__name__)
class ProcessingEngine:
    def __init__(self, input_file, output_dir, log_callback):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.log_callback = log_callback
        self.harvester = DataHarvester()
        output_filename = f"QA_Report_{self.input_file.stem}.xlsx"
        self.output_file = self.output_dir / output_filename
        self.excel_generator = ExcelGenerator(str(self.output_file))
    def run_checks(self):
        self.log_callback(f"Analyzing '{self.input_file.name}'...")
        ext = get_file_extension(self.input_file.name)
        if ext == '.xlsx':
            data = self.harvester.harvest_from_excel(self.input_file)
        elif ext == '.pdf':
            text = extract_text_from_pdf(str(self.input_file))
            data = self.harvester.harvest_from_text(text)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        if not data:
            self.log_callback("No data to process.", "error")
            return
        self.log_callback(f"Found {len(data)} items. Performing QA checks...")
        results = self._perform_qa(data)
        self.log_callback(f"Generating Excel report: {self.output_file}")
        self.excel_generator.create_report(results)
        self.log_callback("Report generation complete.", "success")
    def _perform_qa(self, data):
        # This is where the real QA logic lives.
        # We've restored it with example checks.
        results = []
        for index, item in enumerate(data):
            notes = []
            status = "Passed"
            # Ensure item is a dictionary
            if not isinstance(item, dict):
                self.log_callback(f"Skipping malformed item at row {index + 2}", "warning")
                continue
            
            # Check 1: Missing short description
            short_desc = item.get('short_description', '')
            if not short_desc or (isinstance(short_desc, float) and pd.isna(short_desc)):
                notes.append("Missing 'short_description'.")
                status = "Failed"
                self.log_callback(f"Item {item.get('number', 'N/A')}: FAILED - Missing description.", "error")
            
            # Check 2: Placeholder text in description
            elif 'todo' in str(short_desc).lower() or 'tbd' in str(short_desc).lower():
                notes.append("Placeholder text (TODO/TBD) found in description.")
                status = "Warning"
                self.log_callback(f"Item {item.get('number', 'N/A')}: WARNING - Placeholder text found.", "warning")

            else:
                self.log_callback(f"Item {item.get('number', 'N/A')}: PASSED", "info")

            item['QA Status'] = status
            item['Notes'] = ' | '.join(notes) if notes else "OK"
            results.append(item)
        return results
""",

    # --- kyo_qa_tool_app.py ---
    "kyo_qa_tool_app.py": """
# kyo_qa_tool_app.py
import tkinter as tk
from tkinter import messagebox
import logging
import threading
from gui_components import setup_styles, create_main_header, create_io_section, create_process_controls, create_status_and_log_section, create_status_bar
from processing_engine import ProcessingEngine
from version import get_version
from config import BRAND_COLORS
logger = logging.getLogger('app')

class KyoQAToolApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("KYO QA Knowledge Tool")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        setup_styles()
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True)
        create_main_header(container, get_version(), BRAND_COLORS)
        self.input_path, self.output_path = create_io_section(container, self)
        self.run_button = create_process_controls(container, self.run_qa_check_threaded)
        self.log_text = create_status_and_log_section(container, self)
        self.status_bar = create_status_bar(self.root)
        logger.info("KYO QA Tool initialized successfully")

    def log_message(self, message, level="info"):
        self.root.after(0, self._insert_log_text, message, level)

    def _insert_log_text(self, message, level):
        self.log_text.config(state="normal")
        if "Welcome" in self.log_text.get("1.0", "3.0"):
             self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, f"{message}\\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def run_qa_check_threaded(self):
        self.run_button.config(state="disabled")
        self.status_bar.config(text="Processing...")
        threading.Thread(target=self.run_qa_check, daemon=True).start()

    def run_qa_check(self):
        try:
            input_file = self.input_path.get()
            output_folder = self.output_path.get()
            if not input_file or not output_folder:
                self.root.after(0, lambda: messagebox.showerror("Missing Information", "Please select both an input file and an output folder."))
                return
            self.log_message("Starting QA process...", "info")
            engine = ProcessingEngine(input_file, output_folder, self.log_message)
            engine.run_checks()
            self.root.after(0, lambda: messagebox.showinfo("Success", f"The QA process completed successfully.\\nReport saved to: {engine.output_file}"))
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            self.log_message(error_msg, "error")
            logger.exception("QA process failed")
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        finally:
            self.root.after(0, lambda: self.run_button.config(state="normal"))
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def start(self):
        self.root.mainloop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-5s] %(name)s: %(message)s')
    logger.info("Logger 'app' initialized - KYO QA Tool v%s", get_version())
    app = KyoQAToolApp()
    app.start()
"""
}

# ==============================================================================
#  BEGIN SCRIPT EXECUTION
# ==============================================================================

def repair_all_files():
    """Iterates through the dictionary and writes each file to disk."""
    logging.info("Starting application file repair...")
    current_dir = os.getcwd()
    files_repaired = 0
    
    for filename, content in CORRECT_FILES.items():
        try:
            filepath = os.path.join(current_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content.strip())
            logging.info(f"SUCCESS: Repaired '{filename}'")
            files_repaired += 1
        except Exception as e:
            logging.error(f"FAILED to write '{filename}': {e}")
            
    logging.info("-" * 30)
    if files_repaired == len(CORRECT_FILES):
        logging.info("All core files have been repaired successfully.")
        logging.info("You can now run the main application (run.py or start_tool.py).")
    else:
        logging.error("Some files could not be repaired. Please check messages above.")

if __name__ == "__main__":
    repair_all_files()


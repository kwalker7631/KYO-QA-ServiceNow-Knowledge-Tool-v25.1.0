# KYO QA ServiceNow Knowledge Tool v25.1.0

## Current Version

v25.1.0

## How to Set Up and Run (Modular, Fully Logged)

### 1. Prerequisites

- **Python 3.11.x (64-bit):** Download Python 3.11.9 Windows Installer or use a portable version in `python-3.11.9` folder.
- **Tesseract OCR:** Tesseract Windows Installer (UB Mannheim) or place portable binary in `tesseract` folder.
- **Dependencies:** Listed in `requirements.txt` (auto-installed via `run.py`). Key packages include `PySide6` for the GUI, `PyMuPDF` for PDF handling, `Pillow` for images, `ollama` for AI features, and `extract` for extra data extraction helpers.
- **Install PySide6:** If it doesn't auto-install, run `pip install PySide6` inside the `venv`.

### 2. Folder Structure

KYO_QA_ServiceNow_Knowledge_Tool_v25.1.0/\
├── START.bat\
├── run.py\
├── requirements.txt\
├── README.md\
├── CHANGELOG.md\
├── kyo_qa_tool_app.py\
├── logging_utils.py\
├── ocr_utils.py\
├── ai_extractor.py\
├── data_harvesters.py\
├── excel_generator.py\
├── file_utils.py\
├── processing_engine.py\
├── custom_exceptions.py\
├── version.py\
├── update_version.py\
├── tesseract/ (optional, for portable Tesseract)\
├── python-3.11.9/ (optional, for portable Python)\
├── logs/ (auto-created)\
├── output/ (auto-created)\
└── PDF_TXT/
    └── needs_review/ (auto-created)

## Directory Breakdown

This tool extracts model numbers (e.g., `PF-740`, `TASKalfa AB-1234abcd`, `ECOSYS A123abcd`), QA/SB numbers, and descriptions from Kyocera QA/service PDFs using OCR and pattern recognition. It updates blank cells in the “Meta” column of a cloned ServiceNow-compatible Excel file, preserving the original. Text files for documents needing review are saved in `PDF_TXT/needs_review`. No PDFs are retained.

## 📁 Key Files

| File | Description |
| --- | --- |
| `START.bat` | One-click Windows launcher |
| `run.py` | Initializes environment and starts tool |
| `requirements.txt` | List Python dependencies |
| `README.md` | Setup instructions and usage guide |
| `CHANGELOG.md` | Version history and updates |
| `version.py` | Central version definition |
| `update_version.py` | Update the version across files |

## 🧠 Core Modules

| File | Role |
| --- | --- |
| `kyo_qa_tool_app.py` | Tkinter UI and main controller |
| `processing_engine.py` | Coordinates PDF processing pipeline |
| `ocr_utils.py` | Converts PDF scans to text with OCR (Kanji support) |
| `ai_extractor.py` | Wrapper for data extraction |
| `data_harvesters.py` | Extracts model numbers and metadata |
| `excel_generator.py` | Builds Excel files for ServiceNow import |

## 🔧 Utility Modules

| File | Purpose |
| --- | --- |
| `file_utils.py` | Handles file I/O operations |
| `logging_utils.py` | Log actions to `/logs/` folder |
| `custom_exceptions.py` | Defines custom errors |
| `config.py` | Defines extraction patterns and rules |

## 🗂️ Auto-Generated Folders

| Folder | Description |
| --- | --- |
| `/logs/` | Session logs (success/fail) |
| `/output/` | Excel output (`cloned_<excel>.xlsx`) |
| `/PDF_TXT/needs_review/` | Text files for documents needing review |
| `/venv/` | Virtual environment for isolation |

## ✅ Summary

- **Secure**: No PDF retention.
- **Automated**: Auto-installs dependencies.
- **Portable**: Supports portable Python and Tesseract for USB deployment.
 - **Modular & Logged**: Comprehensive logging to `/logs/` and `PDF_TXT/needs_review` for review.
- **UI**: Bright, Kyocera-branded Tkinter UI with progress bars, color-coded logs, and detailed processing feedback.
- **Excel**: Clones input Excel, updates only blank “Meta” cells with model numbers.

### 3. Setup Steps

1. Place all files in a folder (e.g., `KYO_QA_ServiceNow_Knowledge_Tool_v25.1.0`).
2. Install Python 3.11.x or place portable Python in `python-3.11.9`. Optionally, install Tesseract or place in `tesseract` folder.
3. Run `START.bat` (Windows) or `python run.py`:
   - Sets up `/venv/` and installs dependencies from `requirements.txt`.
   - Outputs logs to `/logs/` and Excel to `/output/`.
4. Manual setup (if needed):

   ```bash

   cd KYO_QA_ServiceNow_Knowledge_Tool_v25.1.0

   rmdir /S /Q venv
   python -m venv venv
   venv\Scripts\python.exe -m ensurepip --default-pip
   venv\Scripts\python.exe -m pip install --upgrade pip
   venv\Scripts\pip.exe install -r requirements.txt
   python kyo_qa_tool_app.py
   ```

### 4. Usage

1. Launch the tool via `START.bat` or `python run.py`.
2. Select an Excel file with a “Meta” column (case-insensitive).
3. Select a folder or PDF files (`.pdf` or `.zip`) containing Kyocera QA/service documents.
4. Click "Start Processing" to:
   - Extract model numbers (e.g., `PF-740`, `TASKalfa AB-1234abcd`), QA numbers, and metadata.
   - Update blank “Meta” cells in a cloned Excel file.
   - Save text files for failed or incomplete extractions in `PDF_TXT/needs_review`.
5. Review output in `/output/cloned_<excel>.xlsx` and logs in `/logs/` or `PDF_TXT/needs_review`.

### Custom Pattern Filtering and Rescan

- Click **Patterns** in the main window to edit regex filters stored in `custom_patterns.py`.
- Use **Re-run Flagged** to process files from the `PDF_TXT/needs_review` folder again.
- Both custom and built-in patterns are applied during each run.

### 5. Development and Testing

Run tests with:

```bash
pytest -q
```

Requires `pandas`, `PyMuPDF`, `PySide6`, `openpyxl`, `pytesseract`, `python-dateutil`, `colorama`, `Pillow`, and `ollama`. Ensure Tesseract is installed or in `tesseract` folder for OCR tests.

### 6. Command-Line Usage (Alpha)

The command line interface is **experimental**. Until the `process_folder` and `process_zip_archive` helpers are fully implemented, the CLI may not run as expected.

You can try it with:

```bash
python cli_runner.py --folder <PDF_folder> --excel <template.xlsx>
```

For progress updates, check the project issue tracker or documentation.

### 7. Versioning

- Current version: **v25.1.0**
- Updates tracked in `CHANGELOG.md`.
- Use `update_version.py` to change versions:

  ```bash
  python update_version.py v25.1.0 v25.1.1
  ```

### 8. Logging

- Session logs in `/logs/[YYYY-MM-DD_HH-MM-SS]_session.log`.
- Success/failure logs as `[YYYYMMDD]_SUCCESSlog.md` or `FAILlog.md` in `/logs/`.
- Text files for documents needing review (e.g., failed model extraction) in `/PDF_TXT/needs_review/*.txt`.
- To also print log messages to the console, call `setup_logger` with `to_console=True`:
  ```python
  from logging_utils import setup_logger
  logger = setup_logger("cli", to_console=True)
  ```

### 9. Portable Deployment

For USB deployment:

1. Place portable Python in `python-3.11.9` folder.
2. Place portable Tesseract in `tesseract` folder.
3. Run `START.bat` to auto-detect portable dependencies.
4. No system-wide installation required.


# KYO QA ServiceNow Knowledge Tool v24.0.6

## How to Set Up and Run (Modular, Fully Logged)

### 1. Prerequisites

- **Python 3.11.x (64-bit):** Download Python 3.11.9 Windows Installer or use a portable version in `python-3.11.9` folder.
- **Tesseract OCR:** Tesseract Windows Installer (UB Mannheim) or place portable binary in `tesseract` folder.
- **Dependencies:** Listed in `requirements.txt` (auto-installed via `start_tool.py`).

### 2. Folder Structure

KYO_QA_ServiceNow_Knowledge_Tool_v24.0.6/\
├── START.bat\
├── start_tool.py\
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
└── PDF_TXT/ (auto-created)

## Directory Breakdown

This tool extracts model numbers (e.g., `PF-740`, `TASKalfa AB-1234abcd`, `ECOSYS A123abcd`), QA/SB numbers, and descriptions from Kyocera QA/service PDFs using OCR and pattern recognition. It updates blank cells in the “Meta” column of a cloned ServiceNow-compatible Excel file, preserving the original. Text files for documents needing review are saved in `PDF_TXT`. No PDFs are retained.

## 📁 Key Files

| File | Description |
| --- | --- |
| `START.bat` | One-click Windows launcher |
| `start_tool.py` | Initializes environment and starts tool |
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
| `/PDF_TXT/` | Text files for documents needing review |
| `/venv/` | Virtual environment for isolation |

## ✅ Summary

- **Secure**: No PDF retention.
- **Automated**: Auto-installs dependencies.
- **Portable**: Supports portable Python and Tesseract for USB deployment.
- **Modular & Logged**: Comprehensive logging to `/logs/` and `PDF_TXT` for review.
- **UI**: Bright, Kyocera-branded Tkinter UI with progress bars, color-coded logs, and detailed processing feedback.
- **Excel**: Clones input Excel, updates only blank “Meta” cells with model numbers.

### 3. Setup Steps

1. Place all files in a folder (e.g., `KYO_QA_ServiceNow_Knowledge_Tool_v24.0.6`).
2. Install Python 3.11.x or place portable Python in `python-3.11.9`. Optionally, install Tesseract or place in `tesseract` folder.
3. Run `START.bat` (Windows) or `python start_tool.py`:
   - Sets up `/venv/` and installs dependencies from `requirements.txt`.
   - Outputs logs to `/logs/` and Excel to `/output/`.
4. Manual setup (if needed):

   ```bash
   cd KYO_QA_ServiceNow_Knowledge_Tool_v24.0.6
   rmdir /S /Q venv
   python -m venv venv
   venv\Scripts\python.exe -m ensurepip --default-pip
   venv\Scripts\python.exe -m pip install --upgrade pip
   venv\Scripts\pip.exe install -r requirements.txt
   python kyo_qa_tool_app.py
   ```

### 4. Usage

1. Launch the tool via `START.bat` or `python start_tool.py`.
2. Select an Excel file with a “Meta” column (case-insensitive).
3. Select a folder or PDF files (`.pdf` or `.zip`) containing Kyocera QA/service documents.
4. Click "Start Processing" to:
   - Extract model numbers (e.g., `PF-740`, `TASKalfa AB-1234abcd`), QA numbers, and metadata.
   - Update blank “Meta” cells in a cloned Excel file.
   - Save text files for failed or incomplete extractions in `PDF_TXT`.
5. Review output in `/output/cloned_<excel>.xlsx` and logs in `/logs/` or `PDF_TXT`.

### 5. Development and Testing

Run tests with:

```bash
pytest -q
```

Requires `pandas`, `PyMuPDF`, `openpyxl`, `pytesseract`, `python-dateutil`, `colorama`. Ensure Tesseract is installed or in `tesseract` folder for OCR tests.

### 6. Versioning

- Current version: **v24.0.6**
- Updates tracked in `CHANGELOG.md`.
- Use `update_version.py` to change versions:

  ```bash
  python update_version.py v24.0.6 v24.0.7
  ```

### 7. Logging

- Session logs in `/logs/[YYYY-MM-DD_HH-MM-SS]_session.log`.
- Success/failure logs as `[YYYYMMDD]_SUCCESSlog.md` or `FAILlog.md` in `/logs/`.
- Text files for documents needing review (e.g., failed model extraction) in `/PDF_TXT/*.txt`.

### 8. Portable Deployment

For USB deployment:

1. Place portable Python in `python-3.11.9` folder.
2. Place portable Tesseract in `tesseract` folder.
3. Run `START.bat` to auto-detect portable dependencies.
4. No system-wide installation required.

**This is the safest, most maintainable, and debug-friendly version yet.**
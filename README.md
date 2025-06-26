# KYO QA ServiceNow Knowledge Tool v24.0.1

## How to Set Up and Run (Modular, Fully Logged)

### 1. Prerequisites
- **Python 3.11.x (64-bit):** [Download Python 3.11.9 Windows Installer](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)
- **Tesseract OCR:** [Tesseract Windows Installer (UB Mannheim)](https://github.com/UB-Mannheim/tesseract/wiki)
- **Optional:** All dependencies listed in `requirements.txt` (auto-installed if you run `start_tool.py`)

### 2. Folder Structure
KYO_QA_ServiceNow_Knowledge_Tool_v24.0.1/
├── run_tool.bat
├── start_tool.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── kyo_qa_tool_app.py
├── logging_utils.py
├── ocr_utils.py
├── ai_extractor.py
├── data_harvesters.py
├── excel_generator.py
├── file_utils.py
├── processing_engine.py
├── custom_exceptions.py
├── logs/(auto-created)
├── output/(auto-created)
└── venv/(auto-created)
# KYO QA ServiceNow Knowledge Tool v24.0.1 – Directory Breakdown

This tool extracts model info, QA/SB numbers, and descriptions from Kyocera QA/service PDFs using OCR + pattern recognition. It outputs a ServiceNow-ready Excel file and logs every step. No PDFs are retained.

---

## 📁 Key Files

| File                | Description                                  |
|---------------------|----------------------------------------------|
| `run_tool.bat`      | One-click Windows launcher                   |
| `start_tool.py`     | Initializes environment and starts tool      |
| `requirements.txt`  | Lists Python dependencies                    |
| `README.md`         | Setup instructions and usage guide           |
| `CHANGELOG.md`      | Version history and updates                  |

---

## 🧠 Core Modules

| File                  | Role                                               |
|------------------------|----------------------------------------------------|
| `kyo_qa_tool_app.py`   | Main controller and orchestrator                  |
| `processing_engine.py` | Coordinates the multi-step processing pipeline    |
| `ocr_utils.py`         | Converts PDF scans to text using OCR              |
| `ai_extractor.py`      | Extracts structured data using regex/NLP          |
| `data_harvesters.py`   | Adds supplemental metadata (e.g., model names)    |
| `excel_generator.py`   | Builds Excel files for ServiceNow import          |

---

## 🔧 Utility Modules

| File                    | Purpose                                   |
|--------------------------|-------------------------------------------|
| `file_utils.py`          | Handles file input/output operations     |
| `logging_utils.py`       | Logs all actions to `/logs/` folder      |
| `custom_exceptions.py`   | Defines custom errors for safe handling  |

---

## 🗂️ Auto-Generated Folders

| Folder     | Description                                   |
|------------|-----------------------------------------------|
| `/logs/`   | Session logs (success/fail)                   |
| `/output/` | Outputs Excel and text files only             |
| `/venv/`   | Local Python environment for isolation        |

---

## ✅ Summary

- **Secure**: Never saves or duplicates original PDFs
- **Automated**: Creates environment, installs requirements
- **Modular & Logged**: Every action is recorded for audit/debug
- **New**: Optional full-screen mode (press `F11`) and a scrolling progress log to
  track each file.



### 3. Setup Steps
1. Place all files above in a single folder.
2. Install Python 3.11.x and Tesseract OCR.
3. Double-click `run_tool.bat` (Windows) or run `python start_tool.py`
   - The tool will set up its virtual environment and auto-install requirements.
    - Logs and output are saved in `/logs/` and `/output/` folders.

### Install Dependencies
If you plan to run or test the tool locally, first install the required Python
packages with the helper script:

```bash
cd KYO_QA_ServiceNow_Knowledge_Tool_v24.0.1
./scripts/setup_env.sh
```

The test suite relies on these packages, so make sure to run the script before
executing `pytest`.

### Development and Testing
After installing the dependencies, run the test suite with:

```bash
pytest -q
```

The tests rely on `pandas`, `PyMuPDF`, and the rest of the packages listed in
`requirements.txt`. If `PyMuPDF` is missing you will see import errors. As of
v24.0.1, unused packages `xlsxwriter` and `halo` were removed to keep the
environment lean.

### 4. Versioning
- This is the modular, logging-enabled release: **v24.0.1**
- Each file and log is stamped with its version.
- All updates are tracked in `CHANGELOG.md`.

### 5. How Logging Works
- Logs for every session/action are saved in `/logs/` as `[YYYYMMDD]FAILlog.md` or `SUCCESSlog.md`.
- Logging is unified across all modules using `logging_utils.py`.
- No output PDF ever lands in `/output/`—only Excel and `.txt` for review.

---

**This is the safest, most maintainable, and debug-friendly version yet.**

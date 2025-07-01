# KYO QA ServiceNow Knowledge Tool v25.1.0

## Current Version

v25.1.0

## How to Set Up and Run (Modular, Fully Logged)

### 1. Prerequisites

- **Python 3.11.x (64-bit):** Download Python 3.11.9 Windows Installer or use a portable version in `python-3.11.9` folder.
- **Tesseract OCR:** Tesseract Windows Installer (UB Mannheim) or place portable binary in `tesseract` folder.
- **Dependencies:** Listed in `requirements.txt` (auto-installed via `start_tool.py`). Key packages include `PySide6` for the GUI, `PyMuPDF` for PDF handling, `Pillow` for images, `ollama` for AI features, and `extract` for extra data extraction helpers.
- **Install PySide6:** If it doesn't auto-install, run `pip install PySide6` inside the `venv`.

### 2. Folder Structure

KYO_QA_ServiceNow_Knowledge_Tool_v25.1.0/\
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
└── PDF_TXT/
    └── needs_review/ (auto-created)

## Directory Breakdown

This tool extracts model numbers (e.g., `PF-740`, `TASKalfa AB-1234abcd`, `ECOSYS A123abcd`), QA/SB numbers, and descriptions from Kyocera QA/service PDFs using OCR and pattern recognition. It updates blank cells in the “Meta” column of a cloned ServiceNow-compatible Excel file, preserving the original. Text files for documents needing review are saved in `PDF_TXT/needs_review`. No PDFs are retained.

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
3. Run `START.bat` (Windows) or `python start_tool.py`:
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

1. Launch the tool via `START.bat` or `python start_tool.py`.
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

You can experiment with a simple CLI by running:

```bash
python cli_runner.py --folder <PDF_folder> --excel <template.xlsx>
```

The CLI currently relies on the upcoming `process_folder` and `process_zip_archive` helpers, so expect limited functionality until those routines are finalized.

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

### 9. Portable Deployment

For USB deployment:

1. Place portable Python in `python-3.11.9` folder.
2. Place portable Tesseract in `tesseract` folder.
3. Run `START.bat` to auto-detect portable dependencies.
4. No system-wide installation required.

**Greg, This is the safest, most maintainable, and debug-friendly version yet.**
Of course. Here is the complete Markdown code for the `README.md` file.

You can copy the code below and save it as `README.md` in your project folder.

```markdown
# KYO QA ServiceNow Knowledge Tool

The KYO QA ServiceNow Knowledge Tool is a desktop application designed to automate the process of extracting key information from PDF documents. It uses Optical Character Recognition (OCR) to handle scanned documents and a flexible pattern-matching system to find product models and other data, which it then populates into a master Excel file.

### **Features**
* **Automated PDF Processing**: Process hundreds of PDF files from a selected folder or by individual selection.
* **OCR for Scanned Documents**: Automatically detects image-based PDFs and uses Tesseract OCR to extract text.
* **Dynamic Pattern Management**: A built-in review tool allows users to add and manage custom Regular Expression (regex) patterns on-the-fly to support new document formats.
* **Rich User Feedback**: The user interface provides real-time feedback on the current process, including a progress bar, colored status indicators, and detailed logs.
* **Automated Environment Setup**: A smart startup script handles the creation of a virtual environment and installation of all required dependencies.

---
## **Installation Guide**
This guide provides instructions for setting up the necessary software on a Windows 11 system.

### **1. Install Python 3.9+**
The application requires Python to run.

* **Download**: Get the **Windows installer (64-bit)** for the latest stable version of Python (e.g., Python 3.11.x) from the official website:
    * **[Python Downloads Page](https://www.python.org/downloads/windows/)**
* **Install and Add to PATH**:
    1.  Run the downloaded installer.
    2.  **Important**: On the first screen of the installer, check the box at the bottom that says **"Add python.exe to PATH."**
    3.  Click **"Install Now"** and follow the on-screen prompts to complete the installation.
* **Verify Installation**:
    1.  Open Command Prompt (`cmd.exe`).
    2.  Type `python --version` and press Enter.
    3.  If it shows a version number (e.g., `Python 3.11.9`), the installation was successful.

### **2. Install Tesseract-OCR**
Tesseract is required for the OCR functionality to read scanned documents.

* **Download**: The recommended installer for Windows is provided by UB Mannheim.
    * **[Tesseract at UB Mannheim Download Page](https://github.com/UB-Mannheim/tesseract/wiki)**
* **Install and Add to PATH**:
    1.  Download and run the `tesseract-ocr-w64-setup-*.exe` installer.
    2.  Proceed through the installation wizard. When you get to the "Select Additional Tasks" screen, ensure that **"Add Tesseract to system PATH for all users"** (or "for current user") is checked.
    3.  Complete the installation.
* **Verify Installation**:
    1.  Open a **new** Command Prompt window.
    2.  Type `tesseract --version` and press Enter.
    3.  If it shows version information (e.g., `tesseract 5.3.4`), the installation was successful.

### **3. Set Up the Application**
With the prerequisites installed, you can now run the tool.

1.  **Icons (Optional)**: For the best visual experience, create a folder named `assets` in the main project directory. Place 16x16 pixel `.png` icons in this folder with the following names: `start.png`, `pause.png`, `stop.png`, `rerun.png`, `open.png`, `browse.png`, `patterns.png`, `exit.png`.
2.  **Run the Launcher**: Simply double-click the **`START.bat`** file.
    * The first time you run it, a setup process will create a virtual environment and install all necessary Python packages. This may take several minutes.
    * Once setup is complete, the main application window will launch automatically.

---
## **How to Use**

1.  **Select Excel File**: Click the first **Browse...** button to select the master `kb_knowledge.xlsx` file you want to use as a template.
2.  **Select PDFs**: Choose either a folder containing all your PDFs or select individual PDF files using the other browse buttons.
3.  **Start Processing**: Click the large red **START** button.
4.  **Monitor Progress**:
    * The **status bar** will change color to show what's happening (Processing, OCR, AI).
    * The **progress bar** will show the overall job completion.
    * The **counters** will update in real-time to show how many files have passed, failed, or need review.
    * The **log viewer** and **live terminal** tabs provide detailed, timestamped messages.

---
## **Managing Extraction Patterns**

When the tool encounters a PDF where it cannot find a model number, it will flag the file for **"Needs Review."** This is your opportunity to teach the tool how to handle new or unusual document formats.

1.  **Identify a File for Review**: After a job completes, look for files in the "Files to Review" list in the UI.
2.  **Open the Pattern Manager**: Click the **Patterns** button in the "Process & Manage" section. This will open the pattern management window.
3.  **Generate a Suggested Pattern**:
    * The text of the PDF will appear on the right side of the window.
    * Find and **highlight** the model number or QA number that the tool missed.
    * Click the **Suggest from Highlight** button. A new regex pattern will be automatically generated in the "Test / Edit Pattern" box.
4.  **Test and Refine**:
    * Click the **Test Pattern** button. All matches found by the new pattern will be highlighted in the text viewer, confirming that it works.
    * You can manually edit the pattern in the box if it needs refinement.
5.  **Add and Save the New Pattern**:
    * Once you're satisfied with the pattern, click **Add as New** or **Update List** to add it to the pattern list on the left.
    * Click the red **Save All Patterns** button. This saves your new pattern to a `custom_patterns.py` file.

The tool will now use your new pattern in all future jobs. For the changes to apply to the currently flagged files, you can use the **Re-run Flagged** button in the main window.
```

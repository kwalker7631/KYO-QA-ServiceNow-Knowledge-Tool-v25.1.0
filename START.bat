@echo off
cls
title KYO QA ServiceNow Tool Launcher

echo --- KYO QA ServiceNow Tool Environment Check ---
echo.

echo [1/4] Checking for Python installation...
where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "python-3.11.9\python.exe" (
        set "PATH=%PATH%;%CD%\python-3.11.9"
        echo      [SUCCESS] Portable Python found.
    ) else (
        echo [ERROR] Python not found. Install Python 3.11+ or place portable Python in 'python-3.11.9' folder.
        goto end_script
    )
)
python --version | findstr "3.11" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11+ required. Current version is not compatible.
    goto end_script
)
echo      [SUCCESS] Python 3.11+ found.

echo.

echo [2/4] Checking for system pip...
python -m pip --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] System pip not found. Install pip: python -m ensurepip && python -m pip install --upgrade pip
    goto end_script
)
echo      [SUCCESS] System pip found.

echo.

echo [3/4] Checking for Tesseract OCR...
where tesseract >nul 2>nul
if %errorlevel% neq 0 (
    if exist "tesseract\tesseract.exe" (
        set "PATH=%PATH%;%CD%\tesseract"
        echo      [SUCCESS] Portable Tesseract found in 'tesseract' folder.
    ) else (
        echo [WARNING] Tesseract not found. Install or place in 'tesseract' folder.
        set TESSERACT_MISSING=1
    )
) else (
    echo      [SUCCESS] Tesseract found in PATH.
)

echo.

echo [4/4] Checking for virtual environment...
if exist "venv\Scripts\python.exe" (
    echo      [SUCCESS] Virtual environment found.
) else (
    echo      [INFO] Virtual environment not found. Will be created.
)

echo.

echo --- Environment check passed. Starting setup... ---
echo.

python start_tool.py
if %errorlevel% neq 0 (
    echo [ERROR] Setup failed. Check logs in 'logs' folder.
    echo [INFO] Try manual setup:
    echo        1. Delete venv folder: rmdir /S /Q venv
    echo        2. Create new venv: python -m venv venv
    echo        3. Activate venv: venv\Scripts\activate
    echo        4. Ensure pip: venv\Scripts\python.exe -m ensurepip --default-pip
    echo        5. Upgrade pip: venv\Scripts\python.exe -m pip install --upgrade pip
    echo        6. Install dependencies: venv\Scripts\pip.exe install -r requirements.txt
    echo        7. Run app: python kyo_qa_tool_app.py
    goto end_script
)

:end_script
echo --------------------------------------------------------
echo.
pause
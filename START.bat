@echo off
cls
title KYO QA ServiceNow Tool Launcher

echo --- KYO QA ServiceNow Tool Environment Check ---
echo.

echo [1/2] Checking for Python installation...
where py.exe >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python from python.org and check "Add Python to PATH".
    goto end_script
)
echo      [SUCCESS] Python is available.

echo.

echo [2/2] Checking for Tesseract OCR installation...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo      [SUCCESS] Tesseract OCR is available.
) else (
    echo [ERROR] Tesseract OCR not found. Please install it to the default path.
    goto end_script
)
echo.

echo --- Environment check passed. Starting Python setup... ---
echo.

:: This is the corrected line. We now call the advanced launcher.
py.exe start_tool.py

:end_script
echo --------------------------------------------------------
echo.
pause
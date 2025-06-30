@echo off
cls
title KYO QA ServiceNow Tool Launcher v25.1.0

echo.
echo --- Initializing KYO QA ServiceNow Tool ---
echo.

:: Set a variable for the python command
set "PYTHON_EXE=python"

:: Check for a portable Python installation first
if exist "python-3.11.9\python.exe" (
    echo [INFO] Portable Python found. Setting path for this session.
    set "PYTHON_EXE=%CD%\python-3.11.9\python.exe"
    echo.
)

:: Verify that a python command is available
%PYTHON_EXE% --version >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ or place a portable version in a 'python-3.11.9' folder.
    goto end_script
)

:: --- Hand off all setup logic to the smart Python script ---
echo [INFO] Found Python. Handing off to start_tool.py for environment setup...
echo.

%PYTHON_EXE% start_tool.py
if %errorlevel% neq 0 (
    echo [ERROR] The startup script failed. Please check the log messages above.
    goto end_script
)

:end_script
echo.
echo --------------------------------------------------------
pause
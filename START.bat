@echo off
title KYO QA Tool Launcher v25.1.2
echo Starting KYO QA ServiceNow Knowledge Tool v25.1.2...
echo This console window will remain open during operation.
python run.py
if %errorlevel% neq 0 (
    echo.
    echo Error starting the application. Please check that Python is installed correctly.
    echo.
    pause
)
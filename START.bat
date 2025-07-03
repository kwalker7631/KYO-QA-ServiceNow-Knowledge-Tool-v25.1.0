@echo off
title KYO QA Tool Launcher v26.0.0
echo Starting KYO QA ServiceNow Knowledge Tool v26.0.0...
echo This console window will remain open during operation.
python run.py
if %errorlevel% neq 0 (
    echo.
    echo Error starting the application. Please check that Python is installed correctly.
    echo.
    pause
)
# KYO QA ServiceNow - Smart Python Launcher with Efficient Setup
from version import VERSION
import argparse
import sys
import subprocess
import shutil
import time
import os
import threading
from pathlib import Path

# Setup basic logging for the startup script itself
from logging_utils import setup_logger, log_info, log_error, log_warning

logger = setup_logger("startup")

# --- UI/Console Enhancements ---
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLOR_INFO = Fore.CYAN
    COLOR_SUCCESS = Fore.GREEN
    COLOR_WARNING = Fore.YELLOW
    COLOR_ERROR = Fore.RED
except ImportError:
    COLOR_INFO = COLOR_SUCCESS = COLOR_WARNING = COLOR_ERROR = ""

# --- Main Setup Functions ---

def print_header():
    """Prints a styled header for the setup process."""
    print("\n" + "=" * 70)
    title = f"KYO QA ServiceNow Tool Smart Setup v{VERSION}"
    padding = (70 - len(title)) // 2
    print(" " * padding + COLOR_INFO + title)
    print("=" * 70 + "\n")

def check_python_version():
    """Ensures the correct Python version is being used."""
    print(f"{COLOR_INFO}[1/4] Checking Python environment...")
    if sys.version_info < (3, 9):
        print(f"{COLOR_ERROR}    ✗ Python 3.9+ is required. You have {sys.version.split()[0]}.")
        return False
    print(f"{COLOR_SUCCESS}    ✓ Python version {sys.version.split()[0]} is compatible.")
    log_info(logger, f"Python version check passed: {sys.version}")
    return True

def setup_virtual_environment():
    """Creates a virtual environment if it doesn't exist or is invalid."""
    print(f"{COLOR_INFO}[2/4] Checking virtual environment...")
    venv_dir = Path.cwd() / "venv"
    if venv_dir.is_dir():
        print(f"{COLOR_SUCCESS}    ✓ Virtual environment already exists.")
        return True
    
    print(f"{COLOR_WARNING}    ⚠ Virtual environment not found. Creating now...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True, capture_output=True)
        print(f"{COLOR_SUCCESS}    ✓ Successfully created virtual environment.")
        log_info(logger, "Virtual environment created.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{COLOR_ERROR}    ✗ Failed to create virtual environment.")
        log_error(logger, f"Venv creation failed: {e.stderr.decode()}")
        return False

def check_and_install_dependencies():
    """
    NEW: Smartly checks dependencies and only installs what's missing.
    """
    print(f"{COLOR_INFO}[3/4] Checking dependencies...")
    venv_python = Path.cwd() / "venv" / "Scripts" / "python.exe"
    req_file = Path.cwd() / "requirements.txt"

    if not venv_python.exists() or not req_file.exists():
        print(f"{COLOR_ERROR}    ✗ Cannot find venv or requirements.txt. Aborting.")
        return False

    try:
        # Get the list of already installed packages in the venv
        installed_raw = subprocess.check_output([str(venv_python), "-m", "pip", "freeze"])
        installed_packages = {line.split('==')[0].lower() for line in installed_raw.decode().splitlines()}
        
        # Read the list of required packages
        with open(req_file, 'r') as f:
            required_packages = {line.strip().split('>=')[0].lower() for line in f if line.strip()}
        
        # Find out what's missing
        missing_packages = required_packages - installed_packages

        if not missing_packages:
            print(f"{COLOR_SUCCESS}    ✓ All dependencies are already installed.")
            log_info(logger, "Dependencies check passed. No new packages needed.")
            return True
        
        print(f"{COLOR_WARNING}    ⚠ Missing packages detected: {', '.join(missing_packages)}. Installing...")
        log_warning(logger, f"Installing missing packages: {missing_packages}")
        
        # Run the installation
        install_command = [str(venv_python), "-m", "pip", "install", "-r", str(req_file)]
        subprocess.run(install_command, check=True, capture_output=True)
        
        print(f"{COLOR_SUCCESS}    ✓ Package installation complete.")
        log_info(logger, "Successfully installed required packages.")
        return True

    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"{COLOR_ERROR}    ✗ An error occurred during dependency installation.")
        log_error(logger, f"Dependency installation failed: {e}")
        return False

def launch_application():
    """Launches the main PySide6 application."""
    print(f"{COLOR_INFO}[4/4] Launching application...")
    venv_python = Path.cwd() / "venv" / "Scripts" / "python.exe"
    app_script = Path.cwd() / "kyo_qa_tool_app.py"

    if not app_script.exists():
        print(f"{COLOR_ERROR}    ✗ Main application script not found: {app_script}")
        return

    print("\n" + "=" * 70)
    print(f"    KYO QA ServiceNow Knowledge Tool v{VERSION} is starting...")
    print("=" * 70 + "\n")
    log_info(logger, f"Launching main app: {app_script}")

    try:
        subprocess.run([str(venv_python), str(app_script)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"{COLOR_ERROR}    ✗ Application failed to start. See error log for details.")
        log_error(logger, f"Application launch failed with exit code {e.returncode}")

def main():
    """Main execution sequence."""
    print_header()
    if not check_python_version(): return
    if not setup_virtual_environment(): return
    if not check_and_install_dependencies(): return
    
    launch_application()

if __name__ == "__main__":
    main()
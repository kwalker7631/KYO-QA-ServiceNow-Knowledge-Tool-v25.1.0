# run.py
import sys
import subprocess
from pathlib import Path
import shutil
import time
import threading

# --- Configuration ---
VENV_DIR = Path(__file__).parent / "venv"
REQUIREMENTS_FILE = Path(__file__).parent / "requirements.txt"
MAIN_APP_SCRIPT = Path(__file__).parent / "kyo_qa_tool_app.py"
MIN_PYTHON_VERSION = (3, 9)

# --- ANSI Colors for "Bling" ---
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Prints the stylized ASCII art header."""
    header = f"""
{Colors.BLUE}
   __  __ __   ____
  | |/ // /  / __ \\
  |   // /  / /_/ /
 /   |/ /_ / ____/
/_/|_/____/_/
{Colors.ENDC}
====================================================
       {Colors.BOLD}KYO QA ServiceNow Knowledge Tool{Colors.ENDC}
====================================================
"""
    print(header)

def run_command_with_spinner(command, message):
    """Runs a command silently while showing a spinner."""
    spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    process_done = threading.Event()

    def spin():
        i = 0
        while not process_done.is_set():
            sys.stdout.write(f"\r{Colors.YELLOW}{spinner_chars[i % len(spinner_chars)]}{Colors.ENDC} {message}")
            sys.stdout.flush()
            i += 1
            time.sleep(0.1)

    spinner_thread = threading.Thread(target=spin, daemon=True)
    spinner_thread.start()

    try:
        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process_done.set()
        spinner_thread.join()
        sys.stdout.write(f"\r{Colors.GREEN}✓{Colors.ENDC} {message}... Done.\n")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        process_done.set()
        spinner_thread.join()
        sys.stdout.write(f"\r{Colors.RED}✗{Colors.ENDC} {message}... Failed.\n")
        return False

def get_venv_python_path():
    """Gets the path to the Python executable in the virtual environment."""
    return VENV_DIR / "Scripts" / "python.exe" if sys.platform == "win32" else VENV_DIR / "bin" / "python"

def setup_environment():
    """Checks Python version, creates venv, and installs dependencies."""
    print_header()

    if sys.version_info < MIN_PYTHON_VERSION:
        print(f"{Colors.RED}✗ Error: Python {'.'.join(map(str, MIN_PYTHON_VERSION))}+ is required.{Colors.ENDC}")
        return False

    venv_python = get_venv_python_path()
    if not (VENV_DIR.exists() and venv_python.exists()):
        print("[INFO] Creating virtual environment...")
        if VENV_DIR.exists(): shutil.rmtree(VENV_DIR)
        if not run_command_with_spinner([sys.executable, "-m", "venv", str(VENV_DIR)], "Creating venv folder"):
            return False
        print("[INFO] Installing dependencies (this may take a few minutes)...")
        if not run_command_with_spinner([str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)], "Installing packages"):
            return False
    
    print(f"{Colors.GREEN}✓ Environment is ready.{Colors.ENDC}")
    return True

def launch_application():
    """Launches the main GUI application and waits for it to close."""
    print(f"\n{Colors.GREEN}--- Launching Application ---{Colors.ENDC}")
    print("[INFO] A console window will remain open for stability. You can minimize it.")
    
    venv_python = get_venv_python_path()
    try:
        subprocess.run([str(venv_python), str(MAIN_APP_SCRIPT)], check=True)
        print(f"\n{Colors.GREEN}--- Application Closed ---{Colors.ENDC}")
    except subprocess.CalledProcessError:
        print(f"\n{Colors.RED}--- APPLICATION CRASHED ---{Colors.ENDC}")
        print(f"{Colors.YELLOW}The application closed unexpectedly. Please review any error messages above.{Colors.ENDC}")
    except FileNotFoundError:
        print(f"\n{Colors.RED}--- LAUNCH FAILED ---{Colors.ENDC}")
        print(f"{Colors.YELLOW}Could not find the application script: {MAIN_APP_SCRIPT}{Colors.ENDC}")

if __name__ == "__main__":
    if setup_environment():
        launch_application()
    
    print("\nPress Enter to exit the launcher.")
    input()
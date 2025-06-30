# start_tool.py
import sys
import subprocess
import threading
import time
from pathlib import Path
import shutil
from version import get_version

# --- Configuration ---
VENV_DIR = Path(__file__).parent / "venv"
REQUIREMENTS_FILE = Path(__file__).parent / "requirements.txt"
MAIN_APP_SCRIPT = Path(__file__).parent / "kyo_qa_tool_app.py"

# --- Global color variables ---
COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_RESET = "", "", "", "", ""

class ConsoleSpinner:
    def __init__(self, message="Working..."):
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.running = False; self.thread = None; self.message = message
    def start(self):
        self.running = True; self.thread = threading.Thread(target=self._spin, daemon=True); self.thread.start()
    def _spin(self):
        i = 0
        while self.running:
            sys.stdout.write(f"\r{COLOR_INFO}{self.spinner_chars[i % len(self.spinner_chars)]} {self.message}{COLOR_RESET}")
            sys.stdout.flush(); i += 1; time.sleep(0.1)
    def stop(self, final_message, success=True):
        self.running = False
        if self.thread: self.thread.join()
        icon = f"{COLOR_SUCCESS}✓{COLOR_RESET}" if success else f"{COLOR_ERROR}✗{COLOR_RESET}"
        sys.stdout.write(f"\r{icon} {final_message}\n"); sys.stdout.flush()

def print_header(version=None):
    version = version or get_version()
    header = f"--- KYO QA ServiceNow Tool Smart Setup v{version} ---"
    print("\n" + "=" * len(header) + "\n" + header + "\n" + "=" * len(header) + "\n")

def run_command(command, spinner_msg):
    spinner = ConsoleSpinner(spinner_msg)
    spinner.start()
    try:
        subprocess.check_call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        spinner.stop(f"{spinner_msg}... Done.", success=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        spinner.stop(f"{spinner_msg}... Failed.", success=False)
        return False

def get_venv_python_path():
    return VENV_DIR / "Scripts" / "python.exe" if sys.platform == "win32" else VENV_DIR / "bin" / "python"

def setup_environment():
    """Ensures Python version is correct and virtual environment is set up."""
    print_header()
    spinner = ConsoleSpinner("Checking Python version...")
    spinner.start()
    if sys.version_info < (3, 9):
        spinner.stop(f"Python 3.9+ is required. You have {sys.version.split()[0]}.", success=False)
        return False
    spinner.stop(f"Python version {sys.version.split()[0]} is compatible.", success=True)
    
    venv_python = get_venv_python_path()
    if VENV_DIR.exists() and venv_python.exists():
        print("✓ Virtual environment folder found.")
        if not run_command([str(venv_python), "-m", "pip", "check"], "Verifying dependencies"):
            print("[WARNING] Dependency check failed. Environment may be corrupt. Rebuilding...")
            return first_time_setup()
    else:
        return first_time_setup()
    return True

def first_time_setup():
    """Runs the detailed, one-time setup for creating the venv and installing packages."""
    print("Starting first-time setup...")
    if VENV_DIR.exists(): shutil.rmtree(VENV_DIR)
    
    if not run_command([sys.executable, "-m", "venv", str(VENV_DIR)], "Creating virtual environment"):
        return False

    venv_python = get_venv_python_path()
    print(f"\n--- Installing Dependencies from {REQUIREMENTS_FILE.name} ---")
    print("This may take a few minutes on first run...\n")
    
    # First upgrade pip
    print("📦 Upgrading pip...")
    try:
        subprocess.check_call([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ Pip upgraded successfully\n")
    except subprocess.CalledProcessError:
        print("⚠ Warning: Could not upgrade pip\n")
    
    # Install packages with visual progress
    command = [str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
    try:
        # Run pip install with real-time output
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                 text=True, encoding='utf-8', errors='replace', bufsize=1)
        
        # Show the output line by line
        for line in iter(process.stdout.readline, ''):
            if line:
                # Clean up the line and print it
                line = line.strip()
                if line.startswith("Collecting") or line.startswith("Installing"):
                    print(f"  {COLOR_INFO}→{COLOR_RESET} {line}")
                elif "Successfully installed" in line:
                    print(f"\n{COLOR_SUCCESS}✓ {line}{COLOR_RESET}")
                elif "already satisfied" in line:
                    # Skip these to reduce clutter
                    pass
                elif line and not line.startswith("  "):
                    print(f"  {line}")
        
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
            
        print(f"\n{COLOR_SUCCESS}✓ All dependencies installed successfully.{COLOR_RESET}")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\n{COLOR_ERROR}✗ Failed to install dependencies.{COLOR_RESET}")
        print(f"Error: {e}")
        return False

def initialize_colors():
    global COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_RESET
    try:
        from colorama import init, Fore, Style
        init(); COLOR_INFO=Fore.CYAN; COLOR_SUCCESS=Fore.GREEN; COLOR_WARNING=Fore.YELLOW; COLOR_ERROR=Fore.RED; COLOR_RESET=Style.RESET_ALL
    except ImportError: pass

def launch_application():
    print(f"\n{COLOR_SUCCESS}--- Launching KYO QA ServiceNow Tool ---{COLOR_RESET}")
    try:
        subprocess.run([str(get_venv_python_path()), str(MAIN_APP_SCRIPT)])
    except Exception as e:
        print(f"\n{COLOR_ERROR}--- APPLICATION CLOSED UNEXPECTEDLY ---")
        print(f"An error occurred: {e}\nPlease check logs for details.")

if __name__ == "__main__":
    if setup_environment():
        initialize_colors()
        launch_application()
    else:
        print("\nSetup failed. Please review messages above.")
    input("\nPress Enter to exit...")
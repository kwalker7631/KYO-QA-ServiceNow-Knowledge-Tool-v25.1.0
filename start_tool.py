# start_tool.py
import sys
import subprocess
import threading
import time
from pathlib import Path
import shutil

# --- Configuration ---
VENV_DIR = Path(__file__).parent / "venv"
WHEEL_CACHE_DIR = Path(__file__).parent / "wheel-cache"
REQUIREMENTS_FILE = Path(__file__).parent / "requirements.txt"
MAIN_APP_SCRIPT = Path(__file__).parent / "kyo_qa_tool_app.py"

# --- Global color variables ---
COLOR_INFO = ""
COLOR_SUCCESS = ""
COLOR_WARNING = ""
COLOR_ERROR = ""
COLOR_RESET = ""

# --- UI Elements for Console ---
class ConsoleSpinner:
    def __init__(self, message="Working..."):
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.running = False
        self.thread = None
        self.message = message

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def _spin(self):
        index = 0
        while self.running:
            char = self.spinner_chars[index % len(self.spinner_chars)]
            sys.stdout.write(f"\r{COLOR_INFO}{char} {self.message}{COLOR_RESET}")
            sys.stdout.flush()
            index += 1
            time.sleep(0.1)

    def stop(self, final_message, success=True):
        self.running = False
        if self.thread:
            self.thread.join()
        icon = f"{COLOR_SUCCESS}✓{COLOR_RESET}" if success else f"{COLOR_ERROR}✗{COLOR_RESET}"
        sys.stdout.write(f"\r{icon} {final_message}\n")
        sys.stdout.flush()

def print_header(version="24.0.6"):
    header = f"--- KYO QA ServiceNow Tool Smart Setup v{version} ---"
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header) + "\n")

def run_pip_command_with_progress(command, error_message):
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"  {output.strip()}")
        return process.wait() == 0
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"{COLOR_ERROR}✗ {error_message}{COLOR_RESET}")
        return False

def get_venv_python_path():
    """Determines the correct path to the python executable in the venv."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"

def setup_environment():
    """Ensures Python version is correct and virtual environment is set up."""
    print_header()

    spinner = ConsoleSpinner("Checking Python version...")
    spinner.start()
    if sys.version_info < (3, 9):
        spinner.stop(f"Python 3.9+ is required. You have {sys.version.split()[0]}.", success=False)
        return False
    spinner.stop(f"Python version {sys.version.split()[0]} is compatible.", success=True)
    
    # --- SIMPLIFIED VENV CHECK ---
    # We only check if the directory exists. If the verification step fails,
    # we will fall back to a full setup.
    if VENV_DIR.exists():
        # --- SUBSEQUENT RUN LOGIC (Fast Path) ---
        print("✓ Virtual environment folder found.")
        venv_python = get_venv_python_path()
        spinner = ConsoleSpinner("Verifying dependencies...")
        spinner.start()
        try:
            # This command is very fast if requirements are already satisfied
            command = [str(venv_python), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
            subprocess.check_call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            spinner.stop("Dependencies verified.", success=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            spinner.stop("Verification failed. Environment may be corrupt.", success=False)
            # Fallback to full setup if verification fails
            return first_time_setup()
            
    else:
        # --- FIRST TIME SETUP LOGIC ---
        return first_time_setup()

    return True

def first_time_setup():
    """Runs the detailed, one-time setup for creating the venv and installing packages."""
    print("Starting first-time setup...")
    
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR)
        
    spinner = ConsoleSpinner("Creating virtual environment...")
    spinner.start()
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        spinner.stop("Virtual environment created successfully.", success=True)
    except subprocess.CalledProcessError:
        spinner.stop("Failed to create virtual environment.", success=False)
        return False

    venv_python = get_venv_python_path()

    # Stage 1: Download packages
    print(f"\n--- Stage 1 of 2: Downloading Packages ---")
    WHEEL_CACHE_DIR.mkdir(exist_ok=True)
    download_command = [str(venv_python), "-m", "pip", "download", "-r", str(REQUIREMENTS_FILE), "-d", str(WHEEL_CACHE_DIR)]
    if not run_pip_command_with_progress(download_command, "Failed to download packages."):
        return False
    print("✓ All package files downloaded successfully.")

    # Stage 2: Install packages one-by-one
    print(f"\n--- Stage 2 of 2: Installing Packages One-by-One ---")
    try:
        with open(REQUIREMENTS_FILE, "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        for i, req in enumerate(requirements, 1):
            spinner = ConsoleSpinner(f"[{i}/{len(requirements)}] Installing {req}...")
            spinner.start()
            command = [str(venv_python), "-m", "pip", "install", "--no-index", f"--find-links={WHEEL_CACHE_DIR}", req]
            subprocess.check_call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            spinner.stop(f"[{i}/{len(requirements)}] Installed {req}.", success=True)

    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"\n{COLOR_ERROR}✗ Failed to install a package from the local cache.{COLOR_RESET}")
        return False

    print("\n✓ All dependencies are installed successfully.")
    shutil.rmtree(WHEEL_CACHE_DIR)
    print("✓ Cleaned up package cache.")
    return True

def initialize_colors():
    """This function is called AFTER dependencies are installed."""
    global COLOR_INFO, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_RESET
    try:
        from colorama import init, Fore, Style
        init()
        COLOR_INFO = Fore.CYAN
        COLOR_SUCCESS = Fore.GREEN
        COLOR_WARNING = Fore.YELLOW
        COLOR_ERROR = Fore.RED
        COLOR_RESET = Style.RESET_ALL
    except ImportError:
        pass

def launch_application():
    """Launches the main Tkinter application."""
    print(f"\n{COLOR_SUCCESS}--- Launching KYO QA ServiceNow Tool ---{COLOR_RESET}")
    venv_python = get_venv_python_path()
    try:
        subprocess.run([str(venv_python), str(MAIN_APP_SCRIPT)])
    except Exception as e:
        print(f"\n{COLOR_ERROR}--- APPLICATION CLOSED UNEXPECTEDLY ---{COLOR_RESET}")
        print(f"An error occurred: {e}")
        print("Please check the logs in the /logs folder for details.")

if __name__ == "__main__":
    if setup_environment():
        initialize_colors()
        launch_application()
    else:
        print("\nSetup failed. Please review the messages above.")
    input("Press Enter to exit...")
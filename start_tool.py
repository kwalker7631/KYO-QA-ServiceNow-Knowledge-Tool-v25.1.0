# start_tool.py — First-run Bootstrapper & Auto Dependency Installer
import subprocess
import sys
import importlib
import os
from pathlib import Path

# Load required packages from external file
REQUIREMENTS_FILE = "requirements.txt"

# Add user scripts directory to PATH if needed
script_path = os.path.expanduser(r"~\AppData\Roaming\Python\Python311\Scripts")
os.environ["PATH"] += os.pathsep + script_path

def load_requirements():
    with open(REQUIREMENTS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def install_package(package):
    try:
        print(f"[INSTALLING] {package}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package, "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"✅ Installed: {package}")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install: {package}")

def check_and_install():
    print("\n--- Python Package Setup (auto-install on first run) ---")
    required_packages = load_requirements()
    for pkg in required_packages:
        try:
            importlib.import_module(pkg.split(".")[0])
            print(f"[✓] Found {pkg}")
        except ImportError:
            install_package(pkg)


def launch_application():

    """Start the GUI application."""
    script = str(Path.cwd() / "kyo_qa_tool_app.py")
    subprocess.run([sys.executable, script], check=True)

if __name__ == "__main__":
    check_and_install()

    # Late import now that all packages are ready
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("[ERROR] PyPDF2 failed to import even after install.")

    print("\n--- All dependencies satisfied. Launching app... ---\n")
main
    launch_application()

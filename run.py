# KYO QA ServiceNow Tool - Python Package Installer v24.0.6
import sys, subprocess, importlib.metadata

try: from version import VERSION
except ImportError: VERSION = "24.0.6"

# FIXED: Added 'ollama' to ensure the AI component can run.
REQUIRED_PACKAGES = ["pandas", "openpyxl", "PyMuPDF", "pytesseract", "ollama"]

def check_and_install_packages():
    print(f"--- Python Package Setup (v{VERSION}) ---")
    all_ready = True
    for i, package in enumerate(REQUIRED_PACKAGES, 1):
        try:
            importlib.metadata.version(package)
            print(f"[{i}/{len(REQUIRED_PACKAGES)}] Found {package}")
        except importlib.metadata.PackageNotFoundError:
            print(f"[{i}/{len(REQUIRED_PACKAGES)}] Missing {package}. Attempting to install...")
            print("-" * 60)
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print("-" * 60)
                print(f"    [SUCCESS] Installed {package}")
            except subprocess.CalledProcessError:
                print("-" * 60); print(f"    [ERROR] FAILED to install {package}.")
                all_ready = False; break
    return all_ready

def launch_main_app():
    print("\n--- Python setup complete. Starting application... ---")
    try: subprocess.run([sys.executable, "kyo_qa_tool_app.py"], check=True)
    except Exception as e: print(f"\n[ERROR] Failed to launch application: {e}")

if __name__ == "__main__":
    if check_and_install_packages():
        launch_main_app()
    else:
        print("\nSetup failed. Please review errors above and run start.bat again.")
        input("\nPress Enter to exit...")

# api_manager.py
import json
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog, messagebox

# --- ADDED: New module to handle API key storage securely. ---

# Use a dedicated, non-version-controlled file to store the API key.
API_CONFIG_FILE = Path(__file__).parent / ".api_config.json"

def save_api_key(key_name: str, key_value: str):
    """Saves an API key to the config file."""
    config = {}
    if API_CONFIG_FILE.exists():
        try:
            with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass  # Overwrite if corrupt or unreadable
    
    config[key_name] = key_value
    
    try:
        with open(API_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except IOError as e:
        messagebox.showerror("API Key Error", f"Could not save API key: {e}")

def load_api_key(key_name: str) -> str | None:
    """Loads an API key from the config file."""
    if not API_CONFIG_FILE.exists():
        return None
    
    try:
        with open(API_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get(key_name)
    except (json.JSONDecodeError, IOError):
        return None

def get_deepl_api_key(parent_window: tk.Toplevel) -> str | None:
    """
    Retrieves the DeepL API key, prompting the user if it's not found.
    """
    api_key = load_api_key("DEEPL_API_KEY")
    if api_key:
        return api_key
    
    # If key is not found, prompt the user.
    key = simpledialog.askstring(
        "DeepL API Key Needed",
        "Please enter your DeepL API key to enable translation.\n"
        "You can get a free key from the DeepL website.",
        parent=parent_window
    )
    
    if key and key.strip():
        save_api_key("DEEPL_API_KEY", key)
        messagebox.showinfo(
            "API Key Saved",
            "Your DeepL API key has been saved successfully.",
            parent=parent_window
        )
        return key
        
    messagebox.showwarning(
        "Translation Disabled",
        "No API key was provided. Translation features will be disabled.",
        parent=parent_window
    )
    return None

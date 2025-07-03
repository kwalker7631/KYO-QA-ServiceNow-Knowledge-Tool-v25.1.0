import json
from pathlib import Path
from queue import Queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import (
    BRAND_COLORS,
    PDF_TXT_DIR,
    CACHE_DIR,
    ASSETS_DIR,
)
from gui_components import (
    create_main_header,
    create_io_section,
    create_process_controls,
    create_status_and_log_section,
)
from version import get_version
from logging_utils import setup_logger

__all__ = ["KyoQAToolApp", "TextRedirector"]


# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------
class TextRedirector:
    """Simple file-like object that redirects written text to a queue."""

    def __init__(self, queue: Queue):
        self.queue = queue

    def write(self, text: str) -> None:  # pragma: no cover - trivial
        if text:
            self.queue.put(text)

    def flush(self) -> None:  # pragma: no cover - compatibility
        pass


# ---------------------------------------------------------------------------
# Basic icon utilities used by the application.
# ---------------------------------------------------------------------------

ICON_MAP = {
    "start": "start.png",
    "pause": "pause.png",
    "stop": "stop.png",
    "rerun": "rerun.png",
    "open": "open.png",
    "browse": "browse.png",
    "patterns": "patterns.png",
    "exit": "exit.png",
    "fullscreen": "fullscreen.png",
}


def load_icon(name: str) -> tk.PhotoImage | None:  # pragma: no cover - GUI helper
    path = ASSETS_DIR / name
    try:
        return tk.PhotoImage(file=path) if path.exists() else None
    except Exception:
        return None


def get_text_icon(key: str) -> str:
    """Return a small unicode fallback for a given icon key."""
    fallbacks = {
        "start": "▶",
        "pause": "❚❚",
        "stop": "■",
        "rerun": "↺",
        "open": "⌗",
        "browse": "…",
        "patterns": "⧉",
        "exit": "✖",
        "fullscreen": "⛶",
    }
    return fallbacks.get(key, "")


def create_default_icons() -> bool:  # pragma: no cover - environment helper
    """Ensure the assets folder exists. Return True if any png files exist."""
    ASSETS_DIR.mkdir(exist_ok=True)
    return any((ASSETS_DIR / fname).exists() for fname in ICON_MAP.values())


# ---------------------------------------------------------------------------
# Application class
# ---------------------------------------------------------------------------
class KyoQAToolApp(tk.Tk):
    """Main GUI application for the KYO QA Tool."""

    def __init__(self) -> None:
        super().__init__()
        self.title("KYO QA Knowledge Tool")
        self.geometry("1000x700")

        # --- Variables used across the UI ---
        self.selected_excel = tk.StringVar()
        self.selected_folder = tk.StringVar()
        self.progress_value = tk.DoubleVar(value=0.0)
        self.status_current_file = tk.StringVar()
        self.time_remaining_var = tk.StringVar()
        self.led_status_var = tk.StringVar()
        self.count_pass = tk.IntVar(value=0)
        self.count_fail = tk.IntVar(value=0)
        self.count_review = tk.IntVar(value=0)
        self.count_ocr = tk.IntVar(value=0)
        self.last_run_info: dict | None = None

        # --- Setup logging ---
        self.log_queue: Queue[str] = Queue()
        self.logger = setup_logger("app", log_widget=None)

        # --- Load icons with graceful fallback ---
        try:
            icons_available = create_default_icons()
            for key, filename in ICON_MAP.items():
                setattr(self, f"{key}_icon", load_icon(filename) if icons_available else None)
        except Exception:
            for key in ICON_MAP:
                setattr(self, f"{key}_icon", None)

        # --- Build UI ---
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)

        create_main_header(container, get_version(), BRAND_COLORS)
        create_io_section(container, self)
        create_process_controls(container, self)
        create_status_and_log_section(container, self)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ------------------------------------------------------------------
    # Event handlers (simplified)
    # ------------------------------------------------------------------
    def start_processing(self) -> None:  # pragma: no cover - GUI behavior
        messagebox.showinfo("Start", "Processing would begin now.")

    def toggle_pause(self) -> None:  # pragma: no cover - GUI behavior
        messagebox.showinfo("Pause", "Processing paused/resumed.")

    def stop_processing(self) -> None:  # pragma: no cover - GUI behavior
        messagebox.showinfo("Stop", "Processing stopped.")

    def rerun_flagged_job(self) -> None:  # pragma: no cover - GUI behavior
        messagebox.showinfo("Re-run", "Re-running flagged documents.")

    def open_result(self) -> None:  # pragma: no cover - GUI behavior
        messagebox.showinfo("Open", "Opening result Excel file.")

    def browse_excel(self) -> None:  # pragma: no cover - GUI behavior
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if path:
            self.selected_excel.set(path)

    def browse_folder(self) -> None:  # pragma: no cover - GUI behavior
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder.set(folder)

    def browse_files(self) -> None:  # pragma: no cover - GUI behavior
        filedialog.askopenfilenames(filetypes=[("PDF", "*.pdf")])

    def open_pattern_manager(self) -> None:  # pragma: no cover - GUI behavior
        messagebox.showinfo("Patterns", "Pattern manager would open.")

    def toggle_fullscreen(self) -> None:  # pragma: no cover - GUI behavior
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def open_review_for_selected_file(self) -> None:  # pragma: no cover - GUI behavior
        messagebox.showinfo("Review", "Review window would open for the file.")

    def on_closing(self) -> None:  # pragma: no cover - GUI behavior
        self.destroy()

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _collect_review_pdfs(self) -> list[str]:
        """Return a list of PDF paths that require manual review."""
        if not self.last_run_info:
            return []

        input_base = Path(self.last_run_info.get("input_path", ""))
        needs_review_dir = PDF_TXT_DIR / "needs_review"
        if not needs_review_dir.exists():
            return []

        review_pdfs: list[str] = []
        for txt_file in needs_review_dir.glob("*.txt"):
            try:
                text = txt_file.read_text(encoding="utf-8")
            except Exception:
                continue

            if "Needs Review" not in text:
                continue

            pdf_name = None
            for line in text.splitlines():
                if line.startswith("File:"):
                    pdf_name = line.split(":", 1)[1].strip()
                    break
            if not pdf_name:
                continue

            candidate = input_base / pdf_name
            if candidate.exists():
                review_pdfs.append(str(candidate))
                continue

            for cache_json in CACHE_DIR.glob(f"{Path(pdf_name).stem}*.json"):
                try:
                    with open(cache_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "pdf_path" in data:
                        review_pdfs.append(data["pdf_path"])
                        break
                except Exception:
                    continue

        return review_pdfs


if __name__ == "__main__":  # pragma: no cover - manual launch
    app = KyoQAToolApp()
    app.mainloop()

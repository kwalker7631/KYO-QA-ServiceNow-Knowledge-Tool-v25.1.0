import argparse
import json
import logging
import os
import subprocess
import traceback
from pathlib import Path

from anthropic import Anthropic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(module)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PATCHES_FILE = Path(".ai_suggestions.json")


def extract_snippet(filename: str, lineno: int, context: int = 5) -> str:
    """Return code snippet around lineno from filename."""
    try:
        lines = Path(filename).read_text().splitlines()
        start = max(0, lineno - context - 1)
        end = min(len(lines), lineno + context)
        snippet = [f"{i+1}: {lines[i]}" for i in range(start, end)]
        return "\n".join(snippet)
    except Exception as exc:  # pragma: no cover - best effort
        logging.error("Failed to extract snippet: %s", exc)
        return ""


def parse_ai_response(content: str) -> dict:
    """Parse AI response content to a dict."""
    try:
        return json.loads(content)
    except Exception:
        return {"raw": content}


def save_suggestion(suggestion: dict) -> None:
    """Persist AI suggestion to disk."""
    suggestions = []
    if PATCHES_FILE.exists():
        try:
            suggestions = json.loads(PATCHES_FILE.read_text())
        except Exception:
            pass
    suggestions.append(suggestion)
    PATCHES_FILE.write_text(json.dumps(suggestions, indent=2))


def report_error_to_ai(exc: Exception, context: dict) -> None:
    """Send exception details to Anthropic and store the suggestion."""
    payload = {
        "error": repr(exc),
        "traceback": traceback.format_exc(),
        "context": context,
        "code_snippet": extract_snippet(context.get("filename", ""), context.get("lineno", 0)),
    }
    prompt = (
        "Here is a Python exception event with context and code.\n"
        "Suggest a patch (file, line numbers, replacement) to fix it:\n"
        f"{json.dumps(payload, indent=2)}"
    )
    try:  # pragma: no cover - external call
        resp = client.messages.create(
            model="claude-3-5-sonnet-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        suggestion = parse_ai_response(resp.content)
        save_suggestion(suggestion)
    except Exception as e:  # pragma: no cover - external failure
        logging.error("Failed to report error to AI: %s", e)


def apply_saved_suggestions() -> None:
    """Apply saved patch suggestions using the `patch` command."""
    if not PATCHES_FILE.exists():
        logging.info("No AI suggestions found")
        return
    suggestions = json.loads(PATCHES_FILE.read_text())
    for suggestion in suggestions:
        patch = suggestion.get("patch") or suggestion.get("raw")
        if not patch:
            continue
        try:
            subprocess.run(["patch", "-p1"], input=patch.encode(), check=True)
        except Exception as exc:  # pragma: no cover - patch may fail
            logging.error("Failed to apply patch: %s", exc)
    PATCHES_FILE.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-suggestions", action="store_true")
    args = parser.parse_args()
    if args.apply_suggestions:
        apply_saved_suggestions()

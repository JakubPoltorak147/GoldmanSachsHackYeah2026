"""Render the AI Control Layer deck to PDF.

The slides live in ``ai-control-layer-presentation.html``; this script prints
that page to ``ai-control-layer-presentation.pdf`` with headless Chrome or Edge.

    py docs/presentation/ai-control-layer-presentation.py

Set ``CHROME_PATH`` to use a specific Chromium-based browser. Fonts are loaded
from Google Fonts, so the first render needs network access.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "ai-control-layer-presentation.html"
OUT = HERE / "ai-control-layer-presentation.pdf"

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
BROWSER_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "chrome", "msedge"]


def find_browser() -> str:
    override = os.environ.get("CHROME_PATH")
    if override:
        return override
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    sys.exit("No Chrome/Edge found; set CHROME_PATH to a Chromium-based browser.")


def main() -> None:
    browser = find_browser()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={profile}",
                "--no-pdf-header-footer",
                "--virtual-time-budget=20000",
                f"--print-to-pdf={OUT}",
                SOURCE.as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
        )
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

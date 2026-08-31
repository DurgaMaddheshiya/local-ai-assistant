"""
launcher.py - Desktop window launcher for Local AI Assistant
Starts FastAPI backend then opens app in a dedicated PyWebView window (no browser needed)
"""

import threading
import time
import sys
import os
import logging

import uvicorn
import webview

# ── logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# ── config ─────────────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 8000
URL  = f"http://{HOST}:{PORT}"


# ── backend thread ─────────────────────────────────────────────────────────
def start_backend():
    """Run FastAPI/uvicorn in a background daemon thread."""
    log.info("Starting backend on %s", URL)
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        log_level="warning",   # keep console clean
        reload=False,
    )


def wait_for_backend(timeout: int = 30) -> bool:
    """Poll until the backend is ready or timeout expires."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{URL}/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.4)
    return False


# ── main ───────────────────────────────────────────────────────────────────
def main():
    # 1. Start backend in background thread
    t = threading.Thread(target=start_backend, daemon=True)
    t.start()

    # 2. Wait until backend is ready
    log.info("Waiting for backend to be ready...")
    if not wait_for_backend():
        log.error("Backend did not start in time. Exiting.")
        sys.exit(1)
    log.info("Backend ready!")

    # 3. Open PyWebView desktop window
    window = webview.create_window(
        title="Local AI Assistant",
        url=URL,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        text_select=True,
    )

    log.info("Opening desktop window at %s", URL)
    webview.start(debug=False)

    log.info("Window closed. Shutting down.")
    sys.exit(0)


if __name__ == "__main__":
    # Must run from project root so 'backend' package is importable
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()

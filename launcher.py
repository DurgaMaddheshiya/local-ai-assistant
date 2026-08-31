"""
launcher.py - Desktop window launcher for Durgara
Starts FastAPI backend then opens app in a dedicated PyWebView window (no browser needed)
"""

import threading
import time
import sys
import os
import logging

import uvicorn
import webview

# â”€â”€ logging â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# â”€â”€ config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
HOST = "127.0.0.1"
PORT = 8000
URL  = f"http://{HOST}:{PORT}"


# â”€â”€ port helper â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def free_port(port: int):
    """Kill whatever process is using the given port (Windows)."""
    import subprocess
    try:
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, capture_output=True, text=True
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and f":{port}" in parts[1]:
                pid = parts[-1]
                subprocess.run(f"taskkill /PID {pid} /F", shell=True,
                               capture_output=True)
                log.info("Killed process %s using port %s", pid, port)
                time.sleep(0.5)
                break
    except Exception as e:
        log.warning("Could not free port %s: %s", port, e)


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOST, port)) == 0


# â”€â”€ backend thread â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def start_backend():
    """Run FastAPI/uvicorn in a background daemon thread."""
    # Free port if already occupied
    if is_port_in_use(PORT):
        log.info("Port %s in use â€” freeing it...", PORT)
        free_port(PORT)
        time.sleep(1)

    log.info("Starting backend on %s", URL)
    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        log_level="warning",
        reload=False,
    )


def wait_for_backend(timeout: int = 30) -> bool:
    """Poll until the backend is ready or timeout expires."""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{URL}/api/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.4)
    return False


# â”€â”€ main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
        title="Durgara",
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


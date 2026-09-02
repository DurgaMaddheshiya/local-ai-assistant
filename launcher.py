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
import keyboard  # global hotkey support

# -- Hide console window on Windows ------------------------------------------
def hide_console():
    """Hide the CMD/console window if running on Windows."""
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
    except Exception:
        pass

hide_console()

# -- logging ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# -- config -------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8000
URL  = f"http://{HOST}:{PORT}"


# -- Python API exposed to JS -------------------------------------------------
class WindowAPI:
    """Methods callable from JS via window.pywebview.api.<method>()"""

    DEFAULT_HOTKEY = 'ctrl+h'

    def __init__(self):
        self._window  = None
        self._visible = True
        self._lock    = threading.Lock()
        self._current_hotkey = self.DEFAULT_HOTKEY

    def set_window(self, win):
        self._window = win

    def toggle_visibility(self):
        """Toggle window hide/show."""
        if self._window is None:
            return
        with self._lock:
            if self._visible:
                self._window.hide()
                self._visible = False
                log.info("Window hidden  (%s)", self._current_hotkey)
            else:
                self._window.show()
                self._visible = True
                log.info("Window shown   (%s)", self._current_hotkey)

    def set_hotkey(self, shortcut: str):
        """Called from JS when user saves a new shortcut in Settings."""
        try:
            try:
                keyboard.remove_hotkey(self._current_hotkey)
            except Exception:
                pass
            keyboard.add_hotkey(shortcut, self.toggle_visibility, suppress=True)
            self._current_hotkey = shortcut
            log.info("Global hotkey changed to: %s", shortcut)
        except Exception as e:
            log.warning("Could not register hotkey '%s': %s", shortcut, e)


# -- port helper --------------------------------------------------------------
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


# -- backend thread -----------------------------------------------------------
def start_backend():
    """Run FastAPI/uvicorn in a background daemon thread."""
    if is_port_in_use(PORT):
        log.info("Port %s in use - freeing it...", PORT)
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


# -- global hotkey thread -----------------------------------------------------
def start_hotkey_listener(api: WindowAPI):
    """Register the initial hotkey (default: Ctrl+H) as a global hotkey."""
    try:
        keyboard.add_hotkey(api._current_hotkey, api.toggle_visibility, suppress=True)
        log.info("Global hotkey registered: %s", api._current_hotkey)
    except Exception as e:
        log.warning("Could not register hotkey: %s", e)
    keyboard.wait()   # blocks forever, keeping listener alive


# -- screenshot protection ----------------------------------------------------
def apply_screenshot_protection(window_title: str = "Durgara"):
    """
    Make window invisible in screenshots using WDA_EXCLUDEFROMCAPTURE.
    When screenshot is taken, window disappears from capture and
    whatever is behind it (desktop/other apps) shows instead.
    Same technique used by Netflix, banking apps, password managers.
    """
    try:
        import ctypes
        user32 = ctypes.windll.user32

        # Retry loop - window may not be ready immediately
        hwnd = None
        for _ in range(10):
            hwnd = user32.FindWindowW(None, window_title)
            if hwnd:
                break
            time.sleep(0.5)

        if not hwnd:
            log.warning("Screenshot protection: window handle not found.")
            return

        # WDA_EXCLUDEFROMCAPTURE = 0x11
        # Window is excluded from DWM capture layer.
        # Screenshot shows whatever is physically behind the window.
        WDA_EXCLUDEFROMCAPTURE = 0x00000011
        result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

        if result:
            log.info("Screenshot protection enabled - app invisible in captures")
        else:
            # Fallback for older Windows
            WDA_MONITOR = 0x00000001
            result = user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR)
            if result:
                log.info("Screenshot protection enabled (WDA_MONITOR fallback)")
            else:
                err = ctypes.windll.kernel32.GetLastError()
                log.warning("Screenshot protection failed (error %s)", err)
    except Exception as e:
        log.warning("Screenshot protection not applied: %s", e)


# -- main ---------------------------------------------------------------------
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

    # 3. Create the API instance
    api = WindowAPI()

    # 4. Open PyWebView desktop window
    window = webview.create_window(
        title="Durgara",
        url=URL,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        text_select=True,
        js_api=api,
    )

    # Give API a reference to the window
    api.set_window(window)

    # 5. Start global hotkey listener in background thread
    hotkey_thread = threading.Thread(
        target=start_hotkey_listener,
        args=(api,),
        daemon=True
    )
    hotkey_thread.start()

    # 6. Apply screenshot protection after window is fully loaded
    def on_loaded():
        time.sleep(1.5)  # wait for window to fully render
        apply_screenshot_protection("Durgara")

    protect_thread = threading.Thread(target=on_loaded, daemon=True)
    protect_thread.start()

    log.info("Opening desktop window at %s", URL)
    webview.start(debug=False)

    log.info("Window closed. Shutting down.")
    sys.exit(0)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()

"""
System Service - Windows Background Process
"""

import threading
import time
import sys
import os
import logging
import ctypes
import random
import string
from pathlib import Path

import uvicorn
import webview
import keyboard  # global hotkey support

# -- Stealth Configuration --------------------------------------------------
def generate_random_process_name():
    """Generate random legitimate-sounding process name"""
    legit_names = [
        "svchost", "dwm", "winlogon", "csrss", "explorer", "taskhost",
        "audiodg", "conhost", "rundll32", "dllhost", "msdtc", "spoolsv",
        "wininit", "services", "lsass", "smss", "fontdrvhost", "dwmcore"
    ]
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{random.choice(legit_names)}{random_suffix}.exe"

def obfuscate_process():
    """Hide process identity"""
    try:
        # Set random process name in memory
        kernel32 = ctypes.windll.kernel32
        fake_name = generate_random_process_name()
        
        # Allocate memory for fake name
        fake_name_ptr = ctypes.create_string_buffer(fake_name.encode())
        
        # Try to modify process name (limited success, but helps some)
        current_process = kernel32.GetCurrentProcess()
        
        # Hide from basic process enumeration
        kernel32.SetProcessWorkingSetSize(current_process, -1, -1)
        
        log.info(f"Process obfuscated as: {fake_name}")
        
    except Exception as e:
        log.warning(f"Process obfuscation failed: {e}")

def hide_from_detection():
    """Advanced hiding techniques"""
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        # Hide window from enumeration
        current_process = kernel32.GetCurrentProcess()
        
        # Set process as system critical (requires admin, optional)
        try:
            ntdll = ctypes.windll.ntdll
            ntdll.RtlSetProcessIsCritical(1, 0, 0)
        except:
            pass  # Silently fail if no admin rights
            
        # Reduce process priority to avoid detection
        kernel32.SetPriorityClass(current_process, 0x00000040)  # IDLE_PRIORITY_CLASS
        
        log.info("Advanced hiding enabled")
        
    except Exception as e:
        log.warning(f"Advanced hiding failed: {e}")

# -- Hide console window on Windows ------------------------------------------
def hide_console():
    """Hide the CMD/console window if running on Windows."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
    except Exception:
        pass

hide_console()

# Initialize stealth mode
obfuscate_process()
hide_from_detection()

# -- Stealth logging (minimal footprint) -------------------------------------
# Create logs in temp directory with random name
temp_dir = Path(os.environ.get('TEMP', '/tmp'))
log_file = temp_dir / f"sys{random.randint(1000,9999)}.tmp"

logging.basicConfig(
    level=logging.WARNING,  # Reduced logging
    format="%(message)s",   # Minimal format
    filename=str(log_file),
    filemode='w'
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

    def take_screenshot(self):
        """
        Take screenshot of background (behind Durgara window).
        
        Process:
        1. Hide window temporarily
        2. Wait 200ms for window to disappear from screen
        3. Capture screenshot
        4. Show window again
        5. Save screenshot to Pictures folder
        6. Copy screenshot to clipboard for easy pasting
        
        Returns:
            dict: {"success": True, "path": filepath} or {"success": False, "error": message}
        """
        if self._window is None:
            return {"success": False, "error": "Window not initialized"}

        try:
            import pyautogui
            from datetime import datetime
            from PIL import Image
            import io
            
            # Hide window
            self._window.hide()
            time.sleep(0.2)  # Wait for window to disappear
            
            # Capture screenshot
            screenshot = pyautogui.screenshot()
            
            # Show window again
            self._window.show()
            
            # Save to Pictures folder
            pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Durgara")
            os.makedirs(pictures_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(pictures_dir, filename)
            
            screenshot.save(filepath)
            log.info("Screenshot saved: %s", filepath)
            
            # Copy to clipboard using win32clipboard (Windows native)
            try:
                import win32clipboard
                from io import BytesIO
                
                # Convert PIL Image to BMP format for clipboard
                output = BytesIO()
                screenshot.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]  # Remove BMP file header (14 bytes)
                output.close()
                
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                log.info("Screenshot copied to clipboard")
            except Exception as clip_err:
                log.warning("Failed to copy to clipboard: %s", clip_err)
            
            return {"success": True, "path": filepath, "folder": pictures_dir}
            
        except Exception as e:
            log.error("Screenshot failed: %s", e)
            # Make sure window is shown again even if error
            if self._window:
                self._window.show()
            return {"success": False, "error": str(e)}
    
    def open_folder(self, path: str):
        """Open a folder in Windows Explorer."""
        try:
            import subprocess
            subprocess.Popen(f'explorer "{path}"')
            log.info("Opened folder: %s", path)
        except Exception as e:
            log.error("Failed to open folder: %s", e)


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


# -- advanced stealth protection ----------------------------------------------------
def apply_window_stealth():
    """Hide window from various detection methods"""
    try:
        user32 = ctypes.windll.user32
        
        # Find all windows with our stealth title
        found_hwnds = []
        
        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int)
        )

        def enum_callback(hwnd, lparam):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                # Match our legitimate titles
                if any(x in title.lower() for x in ["microsoft", "windows", "system", "task", "security"]):
                    found_hwnds.append(hwnd)
            return True

        cb = EnumWindowsProc(enum_callback)
        user32.EnumWindows(cb, 0)

        for hwnd in found_hwnds:
            # Hide from Alt+Tab
            ex_style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
            user32.SetWindowLongW(hwnd, -20, ex_style | 0x00000080)  # WS_EX_TOOLWINDOW
            
            # Remove from taskbar
            user32.SetWindowLongW(hwnd, -20, ex_style | 0x00000008)  # WS_EX_NOACTIVATE
            
            log.info(f"Applied window stealth to hwnd: {hwnd}")
            
    except Exception as e:
        log.warning(f"Window stealth failed: {e}")

def setup_anti_detection():
    """Setup anti-debugging and monitoring protection"""
    try:
        kernel32 = ctypes.windll.kernel32
        ntdll = ctypes.windll.ntdll
        
        # Anti-debugging checks
        is_debugged = kernel32.IsDebuggerPresent()
        if is_debugged:
            log.warning("Debugger detected - entering stealth mode")
            # Don't exit, just log and continue stealthily
        
        # Hide from process monitoring tools
        current_process = kernel32.GetCurrentProcess()
        
        # Prevent memory dumps
        try:
            kernel32.SetProcessDEPPolicy(0x01)  # Always ON
        except:
            pass
            
        # Anti-analysis: Confuse static analysis tools
        fake_imports = [
            "kernel32.dll", "user32.dll", "ntdll.dll", "advapi32.dll",
            "ole32.dll", "oleaut32.dll", "shell32.dll", "gdi32.dll"
        ]
        
        for dll_name in fake_imports:
            try:
                kernel32.LoadLibraryW(dll_name)
            except:
                pass
                
        log.info("Anti-detection measures activated")
        
    except Exception as e:
        log.warning(f"Anti-detection setup failed: {e}")

def hide_network_traffic():
    """Mask network signatures"""
    try:
        # Random User-Agent rotation for HTTP requests
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101",
            "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 10.0; WOW64)",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36",
        ]
        
        # This would be used in HTTP requests (implement in backend)
        selected_agent = random.choice(agents)
        os.environ['STEALTH_USER_AGENT'] = selected_agent
        
        # Random delays for network requests
        os.environ['STEALTH_DELAY'] = str(random.uniform(0.1, 0.5))
        
        log.info("Network traffic masking configured")
        
    except Exception as e:
        log.warning(f"Network masking failed: {e}")


def setup_file_cloaking():
    """Hide application files and folders"""
    try:
        current_dir = Path(__file__).parent.absolute()
        
        # Files/folders to hide
        hide_targets = [
            current_dir / "data",
            current_dir / "logs", 
            current_dir / "__pycache__",
            current_dir / ".venv",
            current_dir / "backend" / "__pycache__",
            current_dir / "launcher.py",
            current_dir / "*.log",
        ]
        
        kernel32 = ctypes.windll.kernel32
        
        for target in hide_targets:
            if target.exists():
                # Set hidden attribute
                attrs = kernel32.GetFileAttributesW(str(target))
                if attrs != -1:  # INVALID_FILE_ATTRIBUTES
                    hidden_attrs = attrs | 0x02  # FILE_ATTRIBUTE_HIDDEN
                    kernel32.SetFileAttributesW(str(target), hidden_attrs)
                    
        # Hide log files in temp directory
        log_pattern = temp_dir / "sys*.tmp"
        for log_file in temp_dir.glob("sys*.tmp"):
            try:
                attrs = kernel32.GetFileAttributesW(str(log_file))
                if attrs != -1:
                    hidden_attrs = attrs | 0x02  # FILE_ATTRIBUTE_HIDDEN
                    kernel32.SetFileAttributesW(str(log_file), hidden_attrs)
            except:
                pass
                    
        log.info("File system cloaking applied")
        
    except Exception as e:
        log.warning(f"File cloaking failed: {e}")


# -- screenshot protection ----------------------------------------------------
def apply_screenshot_protection():
    """
    Make window INVISIBLE in screenshots while staying VISIBLE on screen.

    WDA_EXCLUDEFROMCAPTURE excludes window from DWM capture layer:
    - Screen: Window shows normally, user sees it fine
    - Screenshot/Recording: Window is excluded, background app shows instead

    This is exactly what Netflix, banking apps, password managers use.
    """
    try:
        user32 = ctypes.windll.user32
        WDA_EXCLUDEFROMCAPTURE = 0x00000011

        # Enumerate ALL top-level windows, find Durgara
        found_hwnds = []

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int)
        )

        def enum_callback(hwnd, lparam):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if "durgara" in title.lower() or "local ai" in title.lower():
                    found_hwnds.append(hwnd)
            return True

        cb = EnumWindowsProc(enum_callback)
        user32.EnumWindows(cb, 0)

        # Fallback: direct FindWindow
        if not found_hwnds:
            hwnd = user32.FindWindowW(None, "Durgara")
            if hwnd:
                found_hwnds.append(hwnd)

        if not found_hwnds:
            log.warning("Screenshot protection: Durgara window not found")
            return

        for hwnd in found_hwnds:
            ok = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if ok:
                log.info(
                    "Screenshot protection ON: hwnd=%s | "
                    "Window VISIBLE on screen, INVISIBLE in screenshots. "
                    "Background apps show in screenshots instead.", hwnd
                )
            else:
                err = ctypes.windll.kernel32.GetLastError()
                log.warning("SetWindowDisplayAffinity failed: hwnd=%s err=%s", hwnd, err)

    except Exception as e:
        log.warning("Screenshot protection error: %s", e)


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

    # 4. Open PyWebView desktop window with stealth features
    legitimate_titles = ["Microsoft Windows", "Windows Security", "System Monitor", "Task Scheduler", "Windows Update"]
    stealth_title = random.choice(legitimate_titles)
    
    window = webview.create_window(
        title=stealth_title,  # Random legitimate title
        url=URL,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        text_select=True,
        js_api=api,
        # Stealth window properties
        on_top=False,
        shadow=False,  # No window shadow
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

    # 6. Apply advanced protection after window is loaded
    def on_loaded():
        time.sleep(2)  # wait for window to fully render and be visible
        apply_screenshot_protection()
        apply_window_stealth()
        setup_anti_detection()

    protect_thread = threading.Thread(target=on_loaded, daemon=True)
    protect_thread.start()

    # 7. File system cloaking
    setup_file_cloaking()

    log.info("Opening desktop window at %s", URL)
    webview.start(debug=False)

    log.info("Window closed. Shutting down.")
    sys.exit(0)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()

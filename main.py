"""
main.py — Application Entry Point for LV Nexus v2.1.0
===========================================================

Responsible for:
  - UAC Privilege Elevation
  - Multi-threaded logging initialization
  - Backend/API instantiation
  - PyWebView window orchestration
  - Global error handling
"""

import os
import sys
import json
import logging
import multiprocessing
from typing import Optional

from src.system_utils import SystemUtils
from src.core_engine import OptimizerCore, Config
from src.api_bridge import OptimizerApi

class UILogHandler(logging.Handler):
    """Bridge for streaming Python log records directly to the HTML console."""
    
    def __init__(self, window=None):
        super().__init__()
        self.window = window
        self._in_emit = False

    def set_window(self, window):
        self.window = window

    def emit(self, record: logging.LogRecord):
        # Prevent recursion and ensure we only log "LV_Nexus" namespace
        if not self.window or self._in_emit or not record.name.startswith("LV_Nexus"):
            return
        
        try:
            self._in_emit = True
            msg = self.format(record)
            tag = getattr(record, 'tag', 'SYS')
            # Sanitize for JS
            safe_msg = json.dumps(msg)
            safe_tag = json.dumps(tag)
            js = f"if(window.addLog) window.addLog({safe_tag}, {safe_msg});"
            self.window.evaluate_js(js)
        except Exception:
            # Avoid logging here as it could trigger recursion
            pass
        finally:
            self._in_emit = False

def setup_global_logging() -> logging.Logger:
    """Configures persistent logging to file and standard output."""
    # Silence noisy library loggers that might cause recursion
    logging.getLogger('pywebview').setLevel(logging.WARNING)
    logging.getLogger('comtypes').setLevel(logging.WARNING)
    
    logger = logging.getLogger("LV_Nexus")
    logger.setLevel(logging.DEBUG)
    
    if logger.handlers:
        return logger

    # Path resolution for Logs
    log_dir = os.path.join(os.environ.get('LOCALAPPDATA', '.'), 'LV_Nexus', 'Logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # File Handler
    fh = logging.FileHandler(os.path.join(log_dir, 'runtime.log'), encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    # Stream Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s | [%(levelname)s] | %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def bootstrap():
    """Application initialization sequence."""
    # 1. Enforce Admin Rights
    SystemUtils.elevate()
    
    # 2. Setup Logging
    logger = setup_global_logging()
    ui_handler = UILogHandler()
    
    # 3. Initialize Core
    try:
        core = OptimizerCore()
        api = OptimizerApi(core)
    except Exception as e:
        logger.critical(f"Failed to boot Engine Core: {e}")
        sys.exit(1)

    # 4. Resolve Asset Path
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.dirname(__file__))
    
    html_path = os.path.join(base_path, "gui", "dashboard.html")
    
    # 5. UI Orchestration
    import webview
    
    window = webview.create_window(
        title=f"{Config.APP_NAME} | {Config.VERSION}",
        url=f'file:///{html_path}',
        js_api=api,
        width=1280,
        height=850,
        background_color='#02030a',
        resizable=False,
        min_size=(1200, 800)
    )
    
    api.set_window(window)

    def on_loaded():
        ui_handler.set_window(window)
        logger.addHandler(ui_handler)
        logger.info(f"LV Nexus Engine {Config.VERSION} successfully synchronized.", extra={'tag': 'SYS'})
        logger.info(f"Security Context: {core.status}", extra={'tag': 'SYS'})

    window.events.loaded += on_loaded

    try:
        webview.start(debug=False, private_mode=False)
    except Exception as e:
        logger.critical(f"UI Context Crashed: {e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    bootstrap()

"""
api_bridge.py — Asynchronous Python-to-JavaScript Bridge for LV Nexus v2.1.0
=============================================================================

This module acts as the communication layer between the Python backend and the
HTML5 frontend. It uses the `pywebview` API to expose Python methods to JS
and to evaluate JS expressions for UI updates.

Features:
  - Progress Tracking (evaluated via JS callbacks)
  - Toast Notification dispatching
  - Non-blocking execution using ThreadPoolExecutor
  - Unified System Telemetry
  - Advanced Process Priority Manager endpoints
"""

import logging
import json
from typing import Dict, Any, Optional
from .core_engine import OptimizerCore, Config
from .system_utils import SystemUtils
from .exceptions import LVNexusError

logger = logging.getLogger("LV_Nexus")

class OptimizerApi:
    """API endpoints exposed to the webview frontend."""
    
    def __init__(self, optimizer: OptimizerCore):
        self.opt = optimizer
        self._window = None

    def set_window(self, window) -> None:
        """Attaches the webview window instance for JS evaluation."""
        self._window = window

    # --- UI Callbacks (Internal) ---

    def _eval_js(self, script: str) -> None:
        """Safely evaluates JavaScript in the frontend."""
        if self._window:
            try:
                self._window.evaluate_js(script)
            except Exception as e:
                logger.error(f"JS Evaluation Error: {e}")

    def notify(self, title: str, message: str, type: str = "info") -> None:
        """Triggers a premium toast notification in the UI."""
        safe_title = json.dumps(title)
        safe_msg = json.dumps(message)
        self._eval_js(f"if(window.showToast) window.showToast({safe_title}, {safe_msg}, '{type}');")

    def update_progress(self, percent: int, status: str = "") -> None:
        """Updates the global progress indicator in the UI."""
        safe_status = json.dumps(status)
        self._eval_js(f"if(window.updateProgress) window.updateProgress({percent}, {safe_status});")

    # --- Public API (Exposed to JS) ---

    def get_info(self) -> Dict[str, Any]:
        """Returns static application and hardware info."""
        return {
            'cpu_name': self.opt.cpu_name,
            'total_ram': self.opt.total_ram,
            'ver': self.opt.ver,
            'status': self.opt.status,
            'is_admin': self.opt.is_admin
        }

    def get_telemetry(self) -> Dict[str, Any]:
        """Returns real-time performance metrics."""
        return self.opt.get_hardware_telemetry()

    def get_settings(self) -> Dict[str, Any]:
        """Returns the current engine settings."""
        return self.opt.settings

    def save_settings(self, settings: Dict[str, Any]) -> str:
        """Persists new settings to the core engine."""
        self.opt.update_settings(settings)
        self.notify("Settings Saved", "Global configurations updated successfully.", "success")
        return "OK"

    # --- Actions ---

    def trigger_quick_boost(self) -> str:
        """Starts a quick optimization sequence in a background thread."""
        self.opt.executor.submit(self.opt.quick_boost, self.update_progress)
        return "STARTED"

    def trigger_deep_optimize(self) -> str:
        """Starts a full system optimization in a background thread."""
        def _run():
            try:
                self.opt.deep_optimize(self.update_progress)
            except LVNexusError as e:
                self.notify("System Error", str(e), "error")
        self.opt.executor.submit(_run)
        return "STARTED"

    def apply_profile(self, profile: str) -> str:
        """Applies a performance profile."""
        self.opt.executor.submit(self.opt.apply_profile, profile)
        return "OK"

    def trigger_revert(self) -> str:
        """Emergency system restoration."""
        self.opt.executor.submit(self.opt.reset_system)
        return "REVERT_INITIATED"

    def trigger_ram_purge(self) -> str:
        """Immediate memory reclamation."""
        self.opt.executor.submit(self.opt.nt_kernel_ram_flush)
        self.notify("Memory Purged", "Physical RAM reclaimed successfully.", "success")
        return "OK"

    def trigger_shell_restart(self) -> str:
        """Restarts explorer.exe to apply UI tweaks."""
        def _restart():
            SystemUtils.execute("taskkill /f /im explorer.exe")
            import time
            time.sleep(1)
            SystemUtils.execute("start explorer.exe")
            self.notify("Shell Refreshed", "Windows Explorer has been restarted.", "info")
        
        self.opt.executor.submit(_restart)
        return "OK"

    # --- Bloatware & Startup ---

    def get_startup_apps(self) -> Any:
        """Fetches list of startup applications."""
        return SystemUtils.get_startup_apps()

    def remove_startup_app(self, name: str, is_hklm: bool) -> bool:
        """Removes a startup application entry."""
        success = SystemUtils.remove_startup_app(name, is_hklm)
        if success:
            self.notify("Startup Removed", f"'{name}' will no longer run on boot.", "success")
        else:
            self.notify("Removal Failed", "Could not modify registry.", "error")
        return success

    def get_bloatware(self) -> Any:
        """Fetches the list of monitorable bloatware."""
        return self.opt.get_bloatware()

    def remove_bloatware(self, pkg_id: str) -> bool:
        """Initiates UWP package removal."""
        self.opt.executor.submit(self.opt.remove_bloatware, pkg_id)
        return True

    def trigger_deep_purge(self) -> str:
        """Stand-alone deep system cleanup."""
        def _run():
            self.opt.surgical_purge(self.update_progress)
            self.notify("Purge Complete", "System caches and temporary files sanitized.", "success")
        self.opt.executor.submit(_run)
        return "STARTED"

    # --- Deep Cleaner (BleachBit Style) ---

    def analyze_deep_clean(self) -> Any:
        """Scan all cleaner categories and return size estimates (read-only, safe)."""
        return self.opt.analyze_deep_clean()

    def run_deep_clean(self, category_ids: list) -> str:
        """Execute deep clean for the specified category IDs."""
        def _run():
            result = self.opt.run_deep_clean(category_ids, self.update_progress)
            label = result.get("freed_label", "0 MB")
            cats = len(result.get("categories", []))
            self.notify(
                "🧹 Deep Clean Complete",
                f"Freed {label} across {cats} categories.",
                "success"
            )
        self.opt.executor.submit(_run)
        return "STARTED"

    def get_backups(self) -> Any:
        """Returns the list of available system backups."""
        return self.opt.backup_manager.list_backups()

    def restore_backup(self, ts: str) -> bool:
        """Restores a specific backup version."""
        self.opt.executor.submit(self.opt.backup_manager.perform_rollback, ts)
        return True

    # --- Process Priority Manager ---

    def get_process_list(self) -> Any:
        """Returns a live snapshot of all running processes.

        Called by the Process Manager tab on each refresh cycle.
        Returns a list of dicts: {name, pid, cpu, ram, priority, special}.
        """
        return self.opt.get_process_list()

    def set_process_priority(self, pid: int, priority_key: str) -> bool:
        """Sets the priority class for a single process by PID.

        Args:
            pid:          Target process ID (integer).
            priority_key: One of 'realtime', 'high', 'above_normal',
                          'normal', 'below_normal', 'low'.

        Returns:
            bool: True on success, False otherwise.
        """
        success = self.opt.set_process_priority(pid, priority_key)
        label = priority_key.replace("_", " ").title()
        if success:
            self.notify("Priority Changed", f"PID {pid} → {label}", "success")
        else:
            self.notify("Priority Failed", f"Could not set PID {pid} to {label}.", "error")
        return success

    def pm_boost_gaming(self) -> str:
        """Quick-Boost all gaming processes to HIGH priority."""
        def _run():
            count = self.opt.boost_gaming_processes()
            msg = f"{count} gaming process(es) elevated to HIGH priority."
            self.notify("Gaming Boost Active", msg, "success")
        self.opt.executor.submit(_run)
        return "STARTED"

    def pm_boost_dev(self) -> str:
        """Quick-Boost all development tool processes to HIGH priority."""
        def _run():
            count = self.opt.boost_dev_processes_pm()
            msg = f"{count} dev tool process(es) elevated to HIGH priority."
            self.notify("Dev Boost Active", msg, "success")
        self.opt.executor.submit(_run)
        return "STARTED"

    def pm_reset_all(self) -> str:
        """Reset ALL non-system processes to NORMAL priority."""
        def _run():
            count = self.opt.reset_all_priorities()
            msg = f"All priorities normalized. {count} process(es) reset."
            self.notify("Priorities Reset", msg, "info")
        self.opt.executor.submit(_run)
        return "STARTED"

    # --- Privacy Shield ---

    def get_privacy_status(self) -> Any:
        """Returns all 14 privacy tweaks enriched with live registry 'active' state."""
        return self.opt.get_privacy_status()

    def apply_privacy_settings(self, enabled_ids: list) -> str:
        """Apply tweaks for the given enabled ID list; others revert to default."""
        def _run():
            result = self.opt.apply_privacy_settings(enabled_ids, self.update_progress)
            self.notify(
                "Privacy Shield Applied",
                f"{result['applied']} private, {result['reverted']} default.",
                "success"
            )
        self.opt.executor.submit(_run)
        return "STARTED"

    def apply_privacy_profile(self, profile: str) -> str:
        """Sets all privacy toggles according to a predefined profile."""
        def _run():
            self.opt.apply_privacy_profile(profile, self.update_progress)
            self.notify("Profile Active", f"{profile.upper()} privacy logic synchronized.", "success")
        self.opt.executor.submit(_run)
        return "STARTED"

    # --- Advanced Tweaks (Winaero Style) ---

    def get_advanced_tweaks(self) -> Any:
        """Returns the list of advanced tweaks with live registry status."""
        return self.opt.get_advanced_tweaks_status()

    def apply_advanced_tweaks(self, tweak_ids: list) -> str:
        """Batch apply advanced registry tweaks."""
        def _run():
            success = self.opt.apply_advanced_tweaks(tweak_ids)
            if success:
                self.notify("Tweaks Applied", f"Successfully applied {len(tweak_ids)} advanced tweaks.", "success")
            else:
                self.notify("Tweak Error", "Failed to apply some tweaks. Check logs.", "error")
        self.opt.executor.submit(_run)
        return "STARTED"

    def reset_advanced_tweaks(self) -> str:
        """Reset all advanced tweaks to defaults."""
        def _run():
            self.opt.reset_advanced_tweaks()
            self.notify("Tweaks Reset", "All advanced tweaks restored to defaults.", "info")
        self.opt.executor.submit(_run)
        return "STARTED"

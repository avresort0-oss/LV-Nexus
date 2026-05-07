"""
system_utils.py — Core System Utility Layer for LV Nexus v2.1.0
=============================================================
Wraps low-level Windows operations:
  - Admin privilege detection & UAC elevation
  - Safe subprocess execution with timeout & retry
  - Registry read/write/delete helpers
  - Startup application manager (HKCU + HKLM)

Engineering Standards:
  - Full type hinting (PEP 484)
  - Comprehensive docstrings (Google-style)
  - Granular exception handling with safe fallbacks
  - Thread-safe static methods (no shared mutable state)
"""

import os
import sys
import ctypes
import subprocess
import logging
import winreg
from typing import Dict, List, Optional, Any

import psutil

logger = logging.getLogger("LV_Nexus")


class SystemUtils:
    """Static utility class for safe, thread-safe Windows system operations.

    All methods are static and stateless — safe to call from any thread.
    Admin checks are performed inside methods that require elevation so
    callers receive a clean ``False`` / ``None`` rather than an exception.
    """

    # ------------------------------------------------------------------ #
    #  Admin & Elevation
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_admin() -> bool:
        """Check whether the current process has administrator privileges.

        Returns:
            bool: ``True`` if running as administrator, ``False`` otherwise.
        """
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except OSError as exc:
            logger.error("is_admin OS check failed: %s", exc)
            return False
        except Exception as exc:  # pragma: no cover
            logger.error("is_admin unexpected error: %s", exc)
            return False

    @staticmethod
    def elevate() -> None:
        """Re-launch the current process with UAC elevation if not already admin.

        Spawns a new elevated instance via ``ShellExecuteW`` with the ``runas``
        verb and then exits the current (non-elevated) process.  Has no effect
        if the process is already running as administrator.
        """
        if SystemUtils.is_admin():
            return
        logger.info("[!] Requesting UAC elevation …")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                " ".join(f'"{a}"' for a in sys.argv),
                None,
                1,
            )
        except PermissionError:
            logger.warning("UAC elevation was denied by the user.")
        except Exception as exc:
            logger.error("Failed to request UAC elevation: %s", exc)
        sys.exit(0)

    # ------------------------------------------------------------------ #
    #  Subprocess Execution
    # ------------------------------------------------------------------ #

    @staticmethod
    def execute(
        cmd: str,
        silent: bool = True,
        timeout: int = 45,
        retries: int = 1,
    ) -> Optional[str]:
        """Execute a shell command and return its combined stdout/stderr.

        Args:
            cmd:     The command string to run (passed to ``shell=True``).
            silent:  If ``True``, suppresses the console window on Windows.
            timeout: Maximum seconds to wait before killing the process.
            retries: Number of retry attempts on ``TimeoutExpired``.

        Returns:
            Optional[str]: The stdout string on success; ``None`` on error.

        Note:
            A non-zero return code is logged as a *warning* (not an error)
            because many system commands (e.g. ``net stop``) exit non-zero
            even on partial success.
        """
        flags = subprocess.CREATE_NO_WINDOW if silent else 0

        for attempt in range(max(1, retries)):
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    creationflags=flags,
                    encoding="utf-8",
                    errors="replace",
                )
                if result.returncode != 0:
                    stderr_hint = (result.stderr or result.stdout or "").strip()[:200]
                    logger.warning(
                        "Command rc=%d [%s…]: %s",
                        result.returncode,
                        cmd[:60],
                        stderr_hint,
                    )
                return result.stdout
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Command timed out (attempt %d/%d) after %ds: %s…",
                    attempt + 1,
                    retries,
                    timeout,
                    cmd[:60],
                )
                if attempt >= retries - 1:
                    return None
            except FileNotFoundError:
                logger.error("Executable not found for command: %s…", cmd[:60])
                return None
            except OSError as exc:
                logger.error("OS error executing [%s…]: %s", cmd[:60], exc)
                return None
            except Exception as exc:  # pragma: no cover
                logger.error("Unexpected error executing [%s…]: %s", cmd[:60], exc)
                return None

        return None  # exhausted retries

    # ------------------------------------------------------------------ #
    #  Registry Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def apply_registry_tweak(tweak: Dict[str, str]) -> bool:
        """Apply a single registry value using ``reg.exe``.

        Args:
            tweak: A dict with keys ``'path'``, ``'key'``, ``'type'``,
                   and ``'value'``.

        Returns:
            bool: ``True`` if the tweak was applied; ``False`` on failure.
        """
        required = {"path", "key", "type", "value"}
        if not required.issubset(tweak):
            logger.error("apply_registry_tweak: missing keys in tweak dict %s", tweak)
            return False
        try:
            cmd = (
                f'reg add "{tweak["path"]}" /v "{tweak["key"]}" '
                f'/t {tweak["type"]} /d "{tweak["value"]}" /f'
            )
            out = SystemUtils.execute(cmd, timeout=15)
            if out is None:
                logger.error("Registry tweak failed (None output): %s", tweak["key"])
                return False
            logger.debug("Registry tweak applied: %s -> %s", tweak["path"], tweak["key"])
            return True
        except Exception as exc:
            logger.error("apply_registry_tweak [%s]: %s", tweak.get("key", "?"), exc)
            return False

    @staticmethod
    def remove_registry_tweak(path: str, key: str) -> bool:
        """Remove a registry value.

        Args:
            path: Registry hive + path (e.g. ``HKCU\\Control Panel\\Desktop``).
            key:  The value name to delete.

        Returns:
            bool: ``True`` on success, ``False`` on failure.
        """
        try:
            cmd = f'reg delete "{path}" /v "{key}" /f'
            out = SystemUtils.execute(cmd, timeout=10)
            return out is not None
        except Exception as exc:
            logger.error("remove_registry_tweak [%s]: %s", key, exc)
            return False

    # ------------------------------------------------------------------ #
    #  Startup Application Manager
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_startup_apps() -> List[Dict[str, str]]:
        """Read startup applications from HKCU, HKLM (Run & RunOnce) and Startup folder.

        Returns:
            List[Dict[str, str]]: Each dict has 'name', 'path', 'hklm' (bool), and 'once' (bool).
        """
        apps: List[Dict[str, str]] = []
        _PATHS = [
            (r"Software\Microsoft\Windows\CurrentVersion\Run", False),
            (r"Software\Microsoft\Windows\CurrentVersion\RunOnce", True),
        ]

        # 1. Registry Scan
        for path, is_once in _PATHS:
            # HKCU
            apps.extend(
                SystemUtils._scan_reg_startup(
                    winreg.HKEY_CURRENT_USER, path, False, is_once
                )
            )
            # HKLM
            apps.extend(
                SystemUtils._scan_reg_startup(
                    winreg.HKEY_LOCAL_MACHINE, path, True, is_once
                )
            )

        # 2. Startup Folder Scan
        startup_folder = os.path.join(
            os.environ.get("APPDATA", ""),
            r"Microsoft\Windows\Start Menu\Programs\Startup",
        )
        if os.path.exists(startup_folder):
            for filename in os.listdir(startup_folder):
                if filename.lower().endswith(".lnk"):
                    apps.append(
                        {
                            "name": filename.replace(".lnk", ""),
                            "path": os.path.join(startup_folder, filename),
                            "folder": "true",
                        }
                    )

        return apps

    @staticmethod
    def _scan_reg_startup(
        hive, path: str, is_hklm: bool, is_once: bool
    ) -> List[Dict[str, str]]:
        """Scan a registry hive for startup entries."""
        results: List[Dict[str, str]] = []
        try:
            with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
                idx = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, idx)
                        entry: Dict[str, str] = {"name": name, "path": value}
                        if is_hklm:
                            entry["hklm"] = "true"
                        if is_once:
                            entry["once"] = "true"
                        results.append(entry)
                        idx += 1
                    except OSError:
                        break
        except Exception:
            pass
        return results

    @staticmethod
    def remove_startup_app(
        name: str,
        is_hklm: bool = False,
        is_once: bool = False,
        is_folder: bool = False,
    ) -> bool:
        """Remove a startup entry from Registry or Startup Folder.

        Args:
            name:     The value name to delete from the Run key or .lnk filename.
            is_hklm:  If ``True``, target ``HKLM``; otherwise ``HKCU``.
            is_once:  If ``True``, target the ``RunOnce`` key instead of ``Run``.
            is_folder: If ``True``, treat ``name`` as a shortcut in Startup folder.

        Returns:
            bool: ``True`` on success, ``False`` on any failure.
        """
        # --- Startup Folder removal ---
        if is_folder:
            try:
                startup_folder = os.path.join(
                    os.environ.get("APPDATA", ""),
                    r"Microsoft\Windows\Start Menu\Programs\Startup",
                )
                link_path = os.path.join(startup_folder, f"{name}.lnk")
                if os.path.exists(link_path):
                    os.remove(link_path)
                    logger.info("Startup shortcut removed: %s", name)
                    return True
                logger.warning("Startup shortcut not found: %s", name)
                return False
            except OSError as exc:
                logger.error("OS error removing startup shortcut [%s]: %s", name, exc)
                return False
            except Exception as exc:
                logger.error("Unexpected error removing startup shortcut [%s]: %s", name, exc)
                return False

        # --- Registry removal ---
        run_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        if is_once:
            run_path += "Once"

        root = winreg.HKEY_LOCAL_MACHINE if is_hklm else winreg.HKEY_CURRENT_USER
        hive_label = "HKLM" if is_hklm else "HKCU"

        try:
            key = winreg.OpenKey(root, run_path, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, name)
            winreg.CloseKey(key)
            logger.info("Startup entry removed from %s: %s", hive_label, name)
            return True
        except FileNotFoundError:
            logger.warning("Startup entry not found in %s: %s", hive_label, name)
            return False
        except PermissionError:
            logger.error(
                "Permission denied removing startup entry from %s: %s", hive_label, name
            )
            return False
        except OSError as exc:
            logger.error("OS error removing startup entry [%s]: %s", name, exc)
            return False
        except Exception as exc:
            logger.error("Unexpected error removing startup entry [%s]: %s", name, exc)
            return False

    # ------------------------------------------------------------------ #
    #  Process Priority Manager
    # ------------------------------------------------------------------ #

    # Windows PROCESS priority class constants
    # (used with OpenProcess / SetPriorityClass)
    _PRIORITY_MAP: Dict[str, int] = {
        "realtime": 0x00000100,
        "high": 0x00000080,
        "above_normal": 0x00008000,
        "normal": 0x00000020,
        "below_normal": 0x00004000,
        "low": 0x00000040,
    }

    # Human-readable labels for each psutil priority class integer
    _PRIORITY_LABEL: Dict[int, str] = {
        psutil.REALTIME_PRIORITY_CLASS: "Realtime",
        psutil.HIGH_PRIORITY_CLASS: "High",
        psutil.ABOVE_NORMAL_PRIORITY_CLASS: "Above Normal",
        psutil.NORMAL_PRIORITY_CLASS: "Normal",
        psutil.BELOW_NORMAL_PRIORITY_CLASS: "Below Normal",
        psutil.IDLE_PRIORITY_CLASS: "Low",
    }

    # Apps that should receive a special highlight in the UI
    SPECIAL_APPS: frozenset = frozenset(
        {
            "cursor.exe",
            "code.exe",
            "chrome.exe",
            "valorant.exe",
            "vgc.exe",
            "cs2.exe",
            "steam.exe",
            "pycharm64.exe",
            "idea64.exe",
            "firefox.exe",
            "msedge.exe",
            "obs64.exe",
            "zed.exe",
            "windsurf.exe",
            "blackbox.exe",
            "explorer.exe",
        }
    )

    @staticmethod
    def get_process_list() -> List[Dict[str, Any]]:
        """Return a snapshot of all running processes with key metrics.

        Each entry contains:
            - ``name``     : Process executable name.
            - ``pid``      : Process ID.
            - ``cpu``      : CPU usage percentage (1-second interval sample).
            - ``ram``      : RSS memory usage in MB.
            - ``priority`` : Human-readable priority class string.
            - ``special``  : ``True`` if the process is in the VIP highlight list.

        Returns:
            List[Dict[str, Any]]: Sorted by CPU usage descending.
        """
        processes: List[Dict[str, Any]] = []

        # Collect CPU % with a brief interval (non-blocking — first call returns 0.0)
        # We gather pids first then do a single batch.
        try:
            proc_iter = list(psutil.process_iter(
                ["pid", "name", "cpu_percent", "memory_info", "nice"]
            ))
        except Exception as exc:
            logger.error("get_process_list: iteration failed: %s", exc)
            return []

        for proc in proc_iter:
            try:
                info = proc.info
                name: str = (info.get("name") or "Unknown").strip()
                pid: int = info.get("pid", 0)

                # CPU & RAM
                cpu: float = round(info.get("cpu_percent") or 0.0, 1)
                mem_info = info.get("memory_info")
                ram_mb: float = round(mem_info.rss / (1024 * 1024), 1) if mem_info else 0.0

                # Priority class
                try:
                    nice_val: int = proc.nice()
                    priority_label = SystemUtils._PRIORITY_LABEL.get(nice_val, "Normal")
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    priority_label = "Normal"

                processes.append({
                    "name": name,
                    "pid": pid,
                    "cpu": cpu,
                    "ram": ram_mb,
                    "priority": priority_label,
                    "special": name.lower() in SystemUtils.SPECIAL_APPS,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as exc:
                logger.debug("Skipping process in list: %s", exc)
                continue

        # Sort: special apps first, then by CPU descending
        processes.sort(key=lambda p: (-int(p["special"]), -p["cpu"]))
        return processes[:200]  # Cap at 200 rows for UI performance

    @staticmethod
    def set_process_priority(pid: int, priority_key: str) -> bool:
        """Set the Windows priority class for a running process.

        Args:
            pid:          The process ID to target.
            priority_key: One of: 'realtime', 'high', 'above_normal',
                          'normal', 'below_normal', 'low'.

        Returns:
            bool: ``True`` on success, ``False`` on any failure.

        Note:
            'realtime' requires SYSTEM / administrator privileges.
            All others work fine under a standard elevated user.
        """
        priority_class = SystemUtils._PRIORITY_MAP.get(priority_key.lower())
        if priority_class is None:
            logger.error("set_process_priority: unknown priority key '%s'", priority_key)
            return False

        PROCESS_ALL_ACCESS = 0x1F0FFF
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not handle:
                err = ctypes.get_last_error()
                logger.warning(
                    "set_process_priority: OpenProcess(%d) failed, WinError=%d", pid, err
                )
                return False

            result: bool = bool(kernel32.SetPriorityClass(handle, priority_class))
            kernel32.CloseHandle(handle)

            if result:
                logger.info(
                    "Priority set: PID=%d -> %s (class=0x%X)", pid, priority_key, priority_class
                )
            else:
                err = ctypes.get_last_error()
                logger.warning(
                    "SetPriorityClass failed for PID=%d, WinError=%d", pid, err
                )
            return result

        except Exception as exc:
            logger.error("set_process_priority[PID=%d]: %s", pid, exc)
            return False

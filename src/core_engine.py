"""
core_engine.py — High-Performance Optimization Engine for LV Nexus v2.1.0
========================================================================

This module serves as the central nervous system of the application. It manages
system monitoring, registry-based performance hardening, memory reclamation,
specialized performance profiles, and the Advanced Process Priority Manager.

Key Features:
  - Smart Profile System (Gaming, Development, Content Creation, Balanced)
  - Multi-tier Optimization (Safe vs. Aggressive)
  - Real-time Telemetry (CPU, RAM, GPU, Thermal)
  - Asynchronous Auto-Pilot Daemon
  - Bloatware Sanitization Logic
  - Process Lasso-style Advanced Process Priority Manager

Engineering Standards:
  - PEP8 Compliance
  - Strict Type Hinting
  - Thread-safe Execution
  - Robust Exception Handling with Fallbacks
"""

import os
import sys
import time
import platform
import logging
import threading
import concurrent.futures
import ctypes
from typing import Dict, List, Optional, Set, Any

import psutil
try:
    import GPUtil
except ImportError:
    GPUtil = None

from .system_utils import SystemUtils
from .backup_manager import BackupManager

logger = logging.getLogger("LV_Nexus")

def ui_log(msg: str, tag: str = "SYS", level: int = logging.INFO) -> None:
    """Dispatches log messages to the UI dashboard with specific tagging."""
    extra = {'tag': tag}
    logger.log(level, msg, extra=extra)

class Config:
    """Global immutable configuration and versioning."""
    VERSION: str = "v2.1.0 [PREMIUM]"
    APP_NAME: str = "LV Nexus"

class RegistryVectors:
    """Registry-based performance injections categorized by risk and domain."""
    
    NETWORK: List[Dict[str, str]] = [
        {"path": r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "key": "TcpAckFrequency", "value": "1", "type": "REG_DWORD"},
        {"path": r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "key": "TCPNoDelay", "value": "1", "type": "REG_DWORD"},
        {"path": r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "key": "NetworkThrottlingIndex", "value": "4294967295", "type": "REG_DWORD"},
        {"path": r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters", "key": "DisableBandwidthThrottling", "value": "1", "type": "REG_DWORD"},
    ]
    
    KERNEL: List[Dict[str, str]] = [
        {"path": r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "key": "SystemResponsiveness", "value": "0", "type": "REG_DWORD"},
        {"path": r"HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl", "key": "Win32PrioritySeparation", "value": "38", "type": "REG_DWORD"}, # Hex 0x26 for better foreground focus
        {"path": r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management", "key": "LargeSystemCache", "value": "1", "type": "REG_DWORD"},
    ]
    
    VISUALS: List[Dict[str, str]] = [
        {"path": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "key": "VisualFXSetting", "value": "2", "type": "REG_DWORD"}
    ]

    ADVANCED_TWEAKS: List[Dict[str, Any]] = [
        # --- UI Tweaks ---
        {
            "id": "aero_shake",
            "name": "Disable Aero Shake",
            "desc": "Prevents windows from minimizing when you shake the active window.",
            "category": "UI Tweaks", "risk": "low",
            "path": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            "key": "DisallowShaking", "value": "1", "type": "REG_DWORD"
        },
        {
            "id": "taskbar_transparency",
            "name": "Acrylic Taskbar",
            "desc": "Enhances taskbar transparency (Windows 10/11).",
            "category": "UI Tweaks", "risk": "low",
            "path": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            "key": "TaskbarAcrylicOpacity", "value": "0", "type": "REG_DWORD"
        },
        {
            "id": "verbose_status",
            "name": "Verbose Boot Messages",
            "desc": "Shows detailed service loading messages during startup/shutdown.",
            "category": "Boot Tweaks", "risk": "medium",
            "path": r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
            "key": "verbosestatus", "value": "1", "type": "REG_DWORD"
        },
        # --- Explorer Tweaks ---
        {
            "id": "show_ext",
            "name": "Show File Extensions",
            "desc": "Always display file extensions in Explorer.",
            "category": "Explorer Tweaks", "risk": "low",
            "path": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            "key": "HideFileExt", "value": "0", "type": "REG_DWORD"
        },
        {
            "id": "compact_mode",
            "name": "Explorer Compact Mode",
            "desc": "Reduces vertical padding in File Explorer (Windows 11).",
            "category": "Explorer Tweaks", "risk": "low",
            "path": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            "key": "UseCompactMode", "value": "1", "type": "REG_DWORD"
        },
        {
            "id": "quick_access_clean",
            "name": "Disable Quick Access Junk",
            "desc": "Removes frequently used folders/files from Quick Access.",
            "category": "Explorer Tweaks", "risk": "low",
            "path": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer",
            "key": "ShowFrequent", "value": "0", "type": "REG_DWORD"
        },
        # --- Context Menu ---
        {
            "id": "classic_context",
            "name": "Win11 Classic Menu",
            "desc": "Restores the old right-click menu (No 'Show more options').",
            "category": "Context Menu", "risk": "medium",
            "path": r"HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32",
            "key": "", "value": "", "type": "REG_SZ"
        },
        # --- Network & Perf ---
        {
            "id": "dns_cache",
            "name": "Optimized DNS Caching",
            "desc": "Increases TTL and cache size for faster web browsing.",
            "category": "Network Tweaks", "risk": "low",
            "path": r"HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters",
            "key": "MaxCacheTtl", "value": "86400", "type": "REG_DWORD"
        },
        {
            "id": "irq_priority",
            "name": "IRQ 8 Priority",
            "desc": "Prioritizes CMOS clock for better system timing precision.",
            "category": "Performance", "risk": "high",
            "path": r"HKLM\System\CurrentControlSet\Control\PriorityControl",
            "key": "IRQ8Priority", "value": "1", "type": "REG_DWORD"
        }
    ]

class OptimizerCore:
    """Orchestrates all optimization tasks, system monitoring, safety protocols,
    and the advanced Process Priority Manager."""

    # --- Process Manager: Quick-Boost target sets ---
    GAMING_PROCS: Set[str] = {
        "valorant.exe", "vgc.exe", "cs2.exe", "csgo.exe",
        "steam.exe", "epicgameslauncher.exe", "riotclientservices.exe",
        "leagueclient.exe", "r5apex.exe", "minecraft.exe",
        "gta5.exe", "RainbowSix.exe", "bf2042.exe",
    }

    DEV_PROCS: Set[str] = {
        "cursor.exe", "code.exe", "zed.exe", "pycharm64.exe",
        "idea64.exe", "blackbox.exe", "windsurf.exe",
        "python.exe", "node.exe", "devenv.exe", "rider64.exe",
    }

    BLOATWARE_PACKAGES: List[Dict[str, str]] = [
        {"name": "Microsoft News", "id": "Microsoft.BingNews"},
        {"name": "Weather", "id": "Microsoft.BingWeather"},
        {"name": "Xbox App", "id": "Microsoft.XboxApp"},
        {"name": "Xbox Game Overlay", "id": "Microsoft.XboxGameOverlay"},
        {"name": "Xbox Speech To Text", "id": "Microsoft.XboxSpeechToTextOverlay"},
        {"name": "Skype", "id": "Microsoft.SkypeApp"},
        {"name": "Office Hub", "id": "Microsoft.MicrosoftOfficeHub"},
        {"name": "Solitaire Collection", "id": "Microsoft.MicrosoftSolitaireCollection"},
        {"name": "People", "id": "Microsoft.People"},
        {"name": "Maps", "id": "Microsoft.WindowsMaps"},
        {"name": "Your Phone", "id": "Microsoft.YourPhone"},
        {"name": "Feedback Hub", "id": "Microsoft.WindowsFeedbackHub"},
        {"name": "Get Help", "id": "Microsoft.GetHelp"},
        {"name": "3D Viewer", "id": "Microsoft.Microsoft3DViewer"},
    ]

    # --- Privacy Shield: ShutUp10++ style tweak definitions ---
    PRIVACY_TWEAKS: List[Dict[str, Any]] = [
        # ── Telemetry ──
        {
            "id": "telemetry_level", "name": "Windows Telemetry",
            "category": "Telemetry", "risk": "safe",
            "desc": "Stops Windows from sending diagnostic & usage data to Microsoft servers.",
            "disable": [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "key": "AllowTelemetry", "value": "0", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "key": "AllowTelemetry", "value": "3", "type": "REG_DWORD"}],
        },
        {
            "id": "compat_telemetry", "name": "App Compatibility Telemetry",
            "category": "Telemetry", "risk": "safe",
            "desc": "Disables Microsoft's collection of app compatibility and usage inventory data.",
            "disable": [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat", "key": "AITEnable", "value": "0", "type": "REG_DWORD"},
                        {"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat", "key": "DisableInventory", "value": "1", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat", "key": "AITEnable", "value": "1", "type": "REG_DWORD"},
                        {"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\AppCompat", "key": "DisableInventory", "value": "0", "type": "REG_DWORD"}],
        },
        # ── Search & Cortana ──
        {
            "id": "cortana", "name": "Cortana",
            "category": "Search & Cortana", "risk": "safe",
            "desc": "Disables Cortana AI assistant and its background cloud data collection.",
            "disable": [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search", "key": "AllowCortana", "value": "0", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search", "key": "AllowCortana", "value": "1", "type": "REG_DWORD"}],
        },
        {
            "id": "search_suggestions", "name": "Online Search Suggestions",
            "category": "Search & Cortana", "risk": "safe",
            "desc": "Stops Windows Search from sending your keystrokes to Bing.",
            "disable": [{"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "key": "BingSearchEnabled", "value": "0", "type": "REG_DWORD"},
                        {"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "key": "CortanaConsent", "value": "0", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "key": "BingSearchEnabled", "value": "1", "type": "REG_DWORD"},
                        {"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "key": "CortanaConsent", "value": "1", "type": "REG_DWORD"}],
        },
        # ── Advertising & Tracking ──
        {
            "id": "advertising_id", "name": "Advertising ID",
            "category": "Advertising & Tracking", "risk": "safe",
            "desc": "Disables the unique advertising ID used to track you across apps.",
            "disable": [{"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "key": "Enabled", "value": "0", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "key": "Enabled", "value": "1", "type": "REG_DWORD"}],
        },
        {
            "id": "tailored_ads", "name": "Tailored Experiences",
            "category": "Advertising & Tracking", "risk": "safe",
            "desc": "Prevents Microsoft from using your data to show personalized tips and ads.",
            "disable": [{"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "key": "TailoredExperiencesWithDiagnosticDataEnabled", "value": "0", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Privacy", "key": "TailoredExperiencesWithDiagnosticDataEnabled", "value": "1", "type": "REG_DWORD"}],
        },
        {
            "id": "app_suggestions", "name": "App Suggestions & Silent Installs",
            "category": "Advertising & Tracking", "risk": "safe",
            "desc": "Stops Windows from suggesting and silently installing promoted apps.",
            "disable": [{"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "key": "SilentInstalledAppsEnabled", "value": "0", "type": "REG_DWORD"},
                        {"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "key": "SubscribedContent-338389Enabled", "value": "0", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "key": "SilentInstalledAppsEnabled", "value": "1", "type": "REG_DWORD"},
                        {"path": r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager", "key": "SubscribedContent-338389Enabled", "value": "1", "type": "REG_DWORD"}],
        },
        # ── Location & Sensors ──
        {
            "id": "location", "name": "Location Tracking",
            "category": "Location & Sensors", "risk": "safe",
            "desc": "Disables Windows Location Services for all apps system-wide.",
            "disable": [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors", "key": "DisableLocation", "value": "1", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors", "key": "DisableLocation", "value": "0", "type": "REG_DWORD"}],
        },
        {
            "id": "sensors", "name": "Motion Sensor Data",
            "category": "Location & Sensors", "risk": "safe",
            "desc": "Blocks apps from accessing accelerometer and motion sensor data.",
            "disable": [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors", "key": "DisableSensors", "value": "1", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors", "key": "DisableSensors", "value": "0", "type": "REG_DWORD"}],
        },
        # ── Feedback & Reporting ──
        {
            "id": "feedback", "name": "Windows Feedback Prompts",
            "category": "Feedback & Reporting", "risk": "safe",
            "desc": "Disables the recurring feedback survey prompts from Microsoft.",
            "disable": [{"path": r"HKCU\SOFTWARE\Microsoft\Siuf\Rules", "key": "NumberOfSIUFInPeriod", "value": "0", "type": "REG_DWORD"},
                        {"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "key": "DoNotShowFeedbackNotifications", "value": "1", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKCU\SOFTWARE\Microsoft\Siuf\Rules", "key": "NumberOfSIUFInPeriod", "value": "1", "type": "REG_DWORD"},
                        {"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection", "key": "DoNotShowFeedbackNotifications", "value": "0", "type": "REG_DWORD"}],
        },
        {
            "id": "error_reporting", "name": "Error Reporting (WER)",
            "category": "Feedback & Reporting", "risk": "safe",
            "desc": "Stops Windows from sending crash dumps and error reports to Microsoft.",
            "disable": [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting", "key": "Disabled", "value": "1", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting", "key": "Disabled", "value": "0", "type": "REG_DWORD"}],
        },
        # ── Connected Services ──
        {
            "id": "connected_user_exp", "name": "Connected User Experiences (DiagTrack)",
            "category": "Connected Services", "risk": "moderate",
            "desc": "Disables the DiagTrack background service that continuously uploads usage data.",
            "disable": [{"path": r"HKLM\SYSTEM\CurrentControlSet\Services\DiagTrack", "key": "Start", "value": "4", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SYSTEM\CurrentControlSet\Services\DiagTrack", "key": "Start", "value": "2", "type": "REG_DWORD"}],
        },
        {
            "id": "sync_settings", "name": "Settings Sync (Cloud)",
            "category": "Connected Services", "risk": "safe",
            "desc": "Prevents Windows from syncing passwords and preferences via your Microsoft account.",
            "disable": [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\SettingSync", "key": "DisableSettingSync", "value": "2", "type": "REG_DWORD"},
                        {"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\SettingSync", "key": "DisableSettingSyncUserOverride", "value": "1", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\SettingSync", "key": "DisableSettingSync", "value": "0", "type": "REG_DWORD"},
                        {"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\SettingSync", "key": "DisableSettingSyncUserOverride", "value": "0", "type": "REG_DWORD"}],
        },
        {
            "id": "activity_history", "name": "Activity History (Timeline)",
            "category": "Connected Services", "risk": "safe",
            "desc": "Stops Windows from recording your activity history and syncing it to the cloud.",
            "disable": [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System", "key": "EnableActivityFeed", "value": "0", "type": "REG_DWORD"},
                        {"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System", "key": "PublishUserActivities", "value": "0", "type": "REG_DWORD"}],
            "enable":  [{"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System", "key": "EnableActivityFeed", "value": "1", "type": "REG_DWORD"},
                        {"path": r"HKLM\SOFTWARE\Policies\Microsoft\Windows\System", "key": "PublishUserActivities", "value": "1", "type": "REG_DWORD"}],
        },
    ]

    # Privacy profile definitions: tweak IDs enabled in each profile
    _PRIVACY_PROFILE_MAXIMUM: List[str] = [
        "telemetry_level", "compat_telemetry", "cortana", "search_suggestions",
        "advertising_id", "tailored_ads", "app_suggestions", "location", "sensors",
        "feedback", "error_reporting", "connected_user_exp", "sync_settings", "activity_history",
    ]
    _PRIVACY_PROFILE_BALANCED: List[str] = [
        "telemetry_level", "cortana", "advertising_id", "tailored_ads",
        "app_suggestions", "feedback", "error_reporting", "activity_history",
    ]

    
    def __init__(self) -> None:
        self.ver: str = Config.VERSION
        self.cpu_name: str = platform.processor()[:45]
        self.total_ram: str = f"{round(psutil.virtual_memory().total / (1024 ** 3), 2)} GB"
        self.is_admin: bool = SystemUtils.is_admin()
        self.status: str = "SECURED" if self.is_admin else "LIMITED"
        
        # Thread Management
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=8, thread_name_prefix="OptCore")
        self._lock = threading.Lock()
        
        # Managers
        self.backup_manager = BackupManager()
        
        # State & Settings
        self.auto_pilot_active: bool = True
        self.settings: Dict[str, Any] = {
            "safe_mode": True,
            "aggressive_mode": False,
            "auto_pilot": True,
            "apply_network": True,
            "apply_ui": False
        }
        
        # Bloatware Definitions
        self.bloatwares: List[Dict[str, str]] = [
            {"id": "*Microsoft.3DBuilder*", "name": "3D Builder"},
            {"id": "*Microsoft.BingNews*", "name": "Bing News"},
            {"id": "*Microsoft.GetHelp*", "name": "Get Help"},
            {"id": "*Microsoft.MicrosoftOfficeHub*", "name": "Office Hub"},
            {"id": "*Microsoft.SkypeApp*", "name": "Skype"},
            {"id": "*Microsoft.ZuneMusic*", "name": "Groove Music"},
            {"id": "*Microsoft.ZuneVideo*", "name": "Movies & TV"},
            {"id": "*king.com.CandyCrush*", "name": "Candy Crush"}
        ]
        
        # Hardware Telemetry Cache
        self._telemetry_cache: Dict[str, Any] = {}
        
        # Initialize Background Tasks
        threading.Thread(target=self._auto_pilot_daemon, daemon=True, name="AutoPilot").start()
        ui_log("Optimizer Engine v2.1.0 Initialized.", "SYS")

    # --- Core Settings ---
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """Atomically updates engine settings."""
        with self._lock:
            self.settings.update(new_settings)
            self.auto_pilot_active = self.settings.get("auto_pilot", True)
        ui_log("Global configurations synchronized.", "SYS")

    # --- System Monitoring & Daemon ---

    # --- THERMAL ZONES ---
    TEMP_COOL     = 65   # Below → Aggressive Boost allowed
    TEMP_WARM     = 80   # 65–80 → Balanced Mode
    # Above TEMP_WARM  → Throttle Mode

    # Tracks last known thermal mode for debounce / logging
    _last_thermal_mode: str = ""

    def _auto_pilot_daemon(self) -> None:
        """Background monitoring thread with Smart Temperature-based Adaptive Boost."""
        while True:
            if not self.auto_pilot_active:
                time.sleep(5)
                continue

            try:
                cpu   = psutil.cpu_percent(interval=1)
                ram   = psutil.virtual_memory().percent
                state = self._get_thermal_state()   # {cpu_temp, gpu_temp, mode}

                mode      = state["mode"]
                cpu_temp  = state["cpu_temp"]
                gpu_temp  = state["gpu_temp"]

                # ── Log on mode change only (debounce noise) ──────────────
                if mode != self._last_thermal_mode:
                    emoji = {"cool": "🟢", "warm": "🟡", "hot": "🔴"}.get(mode, "")
                    ui_log(
                        f"{emoji} Thermal Mode → {mode.upper()} "
                        f"(CPU:{cpu_temp}°C GPU:{gpu_temp}°C)",
                        "THERM", logging.WARNING if mode == "hot" else logging.INFO
                    )
                    self._last_thermal_mode = mode

                # ─────────────────────────────────────────────────────────
                #  COOL  (<65°C)  →  Aggressive Boost allowed
                # ─────────────────────────────────────────────────────────
                if mode == "cool":
                    threshold = 85 if self.settings.get("aggressive_mode") else 92
                    if cpu > threshold or ram > threshold:
                        ui_log(
                            f"Load Anomaly + Cool Temps → Aggressive correction "
                            f"(CPU:{cpu}% RAM:{ram}%)", "AI", logging.WARNING
                        )
                        self.nt_kernel_ram_flush(silent=True)
                        self.boost_dev_environment(silent=True)
                        ui_log("Aggressive Boost Applied — System equilibrium restored.", "AI")
                        time.sleep(30)  # Short cooldown in cool zone

                # ─────────────────────────────────────────────────────────
                #  WARM  (65-80°C)  →  Balanced Mode
                # ─────────────────────────────────────────────────────────
                elif mode == "warm":
                    # Only intervene on high load — no aggressive boosts
                    if cpu > 90 or ram > 90:
                        ui_log(
                            f"Balanced Mode: High load at warm temps — soft RAM flush "
                            f"(CPU:{cpu}% RAM:{ram}% Temp:{cpu_temp}°C)", "AI"
                        )
                        self.nt_kernel_ram_flush(silent=True)
                        time.sleep(45)

                # ─────────────────────────────────────────────────────────
                #  HOT  (>80°C)  →  Throttle Mode
                # ─────────────────────────────────────────────────────────
                elif mode == "hot":
                    ui_log(
                        f"🔴 THROTTLE MODE ENGAGED — CPU:{cpu_temp}°C GPU:{gpu_temp}°C. "
                        "Flushing RAM & lowering background priority...",
                        "THERM", logging.WARNING
                    )
                    # 1. Immediate RAM flush
                    self.nt_kernel_ram_flush(silent=True)
                    # 2. Lower background process priorities
                    self._throttle_background_processes()
                    time.sleep(60)  # Long cooldown — let thermals recover

            except Exception as e:
                logger.error(f"Auto-Pilot Exception: {e}")

            time.sleep(5)

    def _get_thermal_state(self) -> Dict[str, Any]:
        """Returns consolidated CPU/GPU temperatures and derived thermal mode.

        Thermal Zones:
            cool  → cpu_temp < 65°C
            warm  → 65 ≤ cpu_temp ≤ 80°C
            hot   → cpu_temp > 80°C

        Falls back gracefully when sensors are unavailable (returns mode='cool').
        """
        cpu_temp = self._get_cpu_temp()
        gpu_temp = 0

        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu_temp = int(gpus[0].temperature)
            except Exception:
                pass

        # Use the higher of CPU/GPU for safety
        peak_temp = max(cpu_temp, gpu_temp)

        if peak_temp == 0:
            # No sensor data — assume cool, do not restrict
            mode = "cool"
        elif peak_temp < self.TEMP_COOL:
            mode = "cool"
        elif peak_temp <= self.TEMP_WARM:
            mode = "warm"
        else:
            mode = "hot"

        return {"cpu_temp": cpu_temp, "gpu_temp": gpu_temp, "mode": mode}

    def _throttle_background_processes(self) -> int:
        """Lowers priority of non-critical background processes to BELOW_NORMAL
        during thermal throttle. Skips system and whitelisted processes.

        Returns:
            int: Number of processes throttled.
        """
        # Whitelist: processes that must never be throttled
        WHITELIST = {
            "system", "registry", "smss.exe", "csrss.exe", "wininit.exe",
            "services.exe", "lsass.exe", "svchost.exe",
            # User-prioritized apps
            "cursor.exe", "code.exe", "zed.exe", "pycharm64.exe",
            "valorant.exe", "cs2.exe",
        }
        count = 0
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                if name in WHITELIST:
                    continue
                pid = proc.info.get("pid", 0)
                if pid and SystemUtils.set_process_priority(pid, "below_normal"):
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception as exc:
                logger.debug("Throttle skip: %s", exc)
        ui_log(f"Throttled {count} background processes to BELOW_NORMAL.", "THERM")
        return count

    def get_thermal_state(self) -> Dict[str, Any]:
        """Public accessor for the current thermal state (used by API/UI)."""
        return self._get_thermal_state()

    def get_hardware_telemetry(self) -> Dict[str, Any]:
        """Collects real-time hardware data with safe fallbacks for missing sensors."""
        try:
            cpu_usage  = psutil.cpu_percent()
            ram_usage  = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('C:').percent

            state      = self._get_thermal_state()
            cpu_temp   = state["cpu_temp"]
            gpu_temp   = state["gpu_temp"]
            therm_mode = state["mode"]

            # GPU load
            gpu_load = 0
            if GPUtil:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu_load = gpus[0].load * 100
                except Exception:
                    pass

            return {
                "cpu":        cpu_usage,
                "ram":        ram_usage,
                "disk":       disk_usage,
                "gpu":        gpu_load,
                "cpu_temp":   cpu_temp,
                "gpu_temp":   gpu_temp,
                "therm_mode": therm_mode,
                "status":     self.status,
            }
        except Exception as e:
            logger.error(f"Telemetry collection failed: {e}")
            return {
                "cpu": 0, "ram": 0, "disk": 0, "gpu": 0,
                "cpu_temp": 0, "gpu_temp": 0,
                "therm_mode": "cool", "status": "ERR"
            }

    def _get_cpu_temp(self) -> int:
        """Retrieves CPU temperature via WMI with multiple namespace fallbacks."""
        # Method 1 — WMI MSAcpi
        try:
            import wmi
            w = wmi.WMI(namespace="root\\wmi")
            temp_data = w.MSAcpi_ThermalZoneTemperature()
            if temp_data:
                return int((temp_data[0].CurrentTemperature / 10.0) - 273.15)
        except Exception:
            pass
        # Method 2 — psutil sensors (Linux/some Windows with LibreHW)
        try:
            sensors = psutil.sensors_temperatures()
            for key in ("coretemp", "cpu_thermal", "acpitz", "k10temp"):
                if key in sensors and sensors[key]:
                    return int(sensors[key][0].current)
        except Exception:
            pass
        return 0

    # --- Optimization Protocols ---

    def create_restore_point(self) -> bool:
        """Triggers a mandatory Windows System Restore point."""
        ui_log("MANDATORY: Creating Windows Restore Point...", "SAFE")
        try:
            cmd = 'powershell -Command "Checkpoint-Computer -Description \'LV_Nexus_Optimization\' -RestorePointType \'MODIFY_SETTINGS\'"'
            SystemUtils.execute(cmd, timeout=120)
            ui_log("Restore point created successfully.", "SAFE")
            return True
        except Exception as e:
            ui_log(f"Restore Point failed: {e}", "ERR", logging.ERROR)
            return False

    def quick_boost(self, progress_callback: Optional[Any] = None) -> None:
        """Non-destructive, fast optimization sequence."""
        ui_log("Executing Rapid System Boost...", "SYS")
        
        steps = [
            (20, "Purging Inactive Memory", self.nt_kernel_ram_flush),
            (60, "Elevating Critical Priorities", self.boost_dev_environment),
            (100, "Finalizing Boost", lambda: ui_log("Quick Boost Complete.", "SYS"))
        ]
        
        for percent, msg, func in steps:
            if progress_callback: progress_callback(percent, msg)
            func()
            time.sleep(0.5)

    def deep_optimize(self, progress_callback: Optional[Any] = None) -> None:
        """Comprehensive kernel and registry hardening protocol."""
        if not self.is_admin:
            ui_log("Access Denied: Deep Optimization requires Administrator rights.", "ERR", logging.ERROR)
            if progress_callback: progress_callback(0, "Permission Error")
            return

        ui_log("Initiating Master Optimization Protocol...", "KERN")
        
        # 1. Safety Layer
        if progress_callback: progress_callback(10, "Establishing Safety Anchor")
        self.create_restore_point()
        self.backup_manager.perform_full_backup()
        
        # 2. Registry Injections
        if progress_callback: progress_callback(30, "Injecting Performance Vectors")
        tweaks = RegistryVectors.KERNEL
        if self.settings.get("apply_network"): tweaks += RegistryVectors.NETWORK
        if self.settings.get("apply_ui"): tweaks += RegistryVectors.VISUALS
        
        for t in tweaks:
            SystemUtils.apply_registry_tweak(t)
            
        # 3. Aggressive Logic
        if self.settings.get("aggressive_mode"):
            ui_log("AGGRESSIVE MODE: Disabling Reserved Storage & Hibernation...", "KERN", logging.WARNING)
            SystemUtils.execute("powercfg -h off")
            SystemUtils.execute("fsutil behavior set disablelastaccess 1")
            
        # 4. System Hygiene
        if progress_callback: progress_callback(60, "Surgical Cache Sanitization")
        self.surgical_purge()
        
        # 5. Finalize
        if progress_callback: progress_callback(100, "Engine Synchronized")
        ui_log("Master Optimization Sequence Finished.", "SYS")

    # --- Profile Management ---

    def apply_profile(self, profile_name: str) -> None:
        """Applies a curated performance profile by name."""
        ui_log(f"Loading Profile: {profile_name.upper()}...", "PRIME")
        
        profile_actions = {
            "gaming": self._profile_gaming,
            "development": self._profile_development,
            "content": self._profile_content,
            "balanced": self._profile_balanced
        }
        
        if profile_name in profile_actions:
            profile_actions[profile_name]()
        else:
            ui_log(f"Unknown profile: {profile_name}", "ERR", logging.ERROR)

    def _profile_gaming(self) -> None:
        self._set_power_plan("ultra")
        self.boost_process_group({"valorant.exe", "cs2.exe", "steam.exe", "epicgameslauncher.exe", "vgc.exe"})
        self._toggle_services("lockdown")
        ui_log("Gaming Profile Active: Network Latency & Process Priority Hardened.", "PRIME")

    def _profile_development(self) -> None:
        self._set_power_plan("ultra")
        self.boost_dev_environment()
        self._toggle_services("recover")
        ui_log("Development Profile Active: IDEs & Compilers Prioritized.", "PRIME")

    def _profile_content(self) -> None:
        self._set_power_plan("ultra")
        self.boost_process_group({"adobe premiere pro.exe", "aftereffects.exe", "obs64.exe", "davinci.exe"})
        self._toggle_services("recover")
        ui_log("Content Profile Active: Multithreaded rendering optimized.", "PRIME")

    def _profile_balanced(self) -> None:
        self._set_power_plan("eco")
        self._toggle_services("recover")
        ui_log("Balanced Profile Active: Efficiency Mode Engaged.", "PRIME")

    # --- Utility Methods (Thread Safe) ---

    def nt_kernel_ram_flush(self, silent: bool = False) -> None:
        """Reclaims physical memory from all non-system processes using native Win32 API."""
        if not silent: ui_log("Purging Physical RAM Standby Lists...", "MEM")
        try:
            kernel32 = ctypes.WinDLL('kernel32')
            psapi = ctypes.WinDLL('psapi')
            
            pids = (ctypes.c_uint32 * 4096)()
            cb_needed = ctypes.c_uint32()
            
            if psapi.EnumProcesses(ctypes.byref(pids), ctypes.sizeof(pids), ctypes.byref(cb_needed)):
                count = cb_needed.value // 4
                for i in range(count):
                    pid = pids[i]
                    if pid == 0: continue
                    h = kernel32.OpenProcess(0x1F0FFF, False, pid)
                    if h:
                        psapi.EmptyWorkingSet(h)
                        kernel32.CloseHandle(h)
            if not silent: ui_log("Memory Flush Successful.", "MEM")
        except Exception as e:
            logger.error(f"RAM Flush Error: {e}")

    def boost_dev_environment(self, silent: bool = False) -> None:
        """Elevates priority for common Development tools."""
        targets = {"cursor.exe", "code.exe", "zed.exe", "pycharm64.exe", "idea64.exe", "blackbox.exe", "windsurf.exe"}
        count = self.boost_process_group(targets)
        if not silent: ui_log(f"Hardened priority for {count} Development environments.", "DEV")

    def boost_process_group(self, targets: Set[str]) -> int:
        """Elevates priority for a set of process names."""
        count = 0
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name'].lower() if proc.info['name'] else ""
                if name in targets:
                    proc.nice(psutil.HIGH_PRIORITY_CLASS)
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return count

    def surgical_purge(self, progress_callback: Optional[Any] = None) -> None:
        """Cleans temporary files and caches for professional tools and OS."""
        ui_log("Sanitizing OS & Application Caches...", "CLEAN")
        
        user_local = os.environ.get('LOCALAPPDATA', '')
        user_appdata = os.environ.get('APPDATA', '')
        windir = os.environ.get('WINDIR', 'C:\\Windows')
        
        # Deep cleaning targets
        targets = [
            ("User Temp", os.path.join(user_local, "Temp")),
            ("Windows Temp", os.path.join(windir, 'Temp')),
            ("Prefetch", os.path.join(windir, 'Prefetch')),
            ("NVIDIA Shader Cache", os.path.join(user_local, "NVIDIA", "DXCache")),
            ("AMD Shader Cache", os.path.join(user_local, "AMD", "DxCache")),
            ("Windows Update Cache", os.path.join(windir, "SoftwareDistribution", "Download")),
            ("Crash Dumps", os.path.join(user_local, "CrashDumps")),
            ("Chrome Cache", os.path.join(user_local, "Google", "Chrome", "User Data", "Default", "Cache")),
            ("Edge Cache", os.path.join(user_local, "Microsoft", "Edge", "User Data", "Default", "Cache")),
            ("Cursor Cache", os.path.join(user_appdata, "Cursor", "Cache")),
            ("VS Code Cache", os.path.join(user_appdata, "Code", "Cache")),
            ("Discord Cache", os.path.join(user_appdata, "discord", "Cache")),
        ]
        
        removed_bytes = 0
        total_items = len(targets)
        
        for i, (name, p) in enumerate(targets):
            if progress_callback:
                progress_callback(int((i/total_items)*100), f"Purging: {name}")
                
            if os.path.exists(p):
                try:
                    for root, dirs, files in os.walk(p, topdown=False):
                        for f in files:
                            try:
                                fp = os.path.join(root, f)
                                removed_bytes += os.path.getsize(fp)
                                os.remove(fp)
                            except Exception: pass
                        for d in dirs:
                            try: os.rmdir(os.path.join(root, d))
                            except Exception: pass
                except Exception as e:
                    logger.debug(f"Could not clean {p}: {e}")
        
        if progress_callback: progress_callback(100, "Cleanup Finished")
        ui_log(f"Cleanup Complete. Reclaimed {round(removed_bytes / (1024*1024), 2)} MB.", "CLEAN")

    def _set_power_plan(self, mode: str) -> None:
        """Switches between high performance and energy efficient plans."""
        if not self.is_admin: return
        plans = {
            "ultra": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", # High Performance
            "eco": "381b4222-f694-41f0-9685-ff5bb260df2e"   # Balanced
        }
        guid = plans.get(mode)
        if guid:
            SystemUtils.execute(f"powercfg /setactive {guid}")

    def _toggle_services(self, mode: str) -> None:
        """Disables or restores non-critical background services."""
        if not self.is_admin: return
        services = ["DiagTrack", "Spooler", "wuauserv", "SysMain", "MapsBroker"]
        for s in services:
            if mode == "lockdown":
                SystemUtils.execute(f"net stop {s}")
                SystemUtils.execute(f"sc config {s} start=disabled")
            else:
                SystemUtils.execute(f"sc config {s} start=auto")
                SystemUtils.execute(f"net start {s}")

    # --- Bloatware Control ---
    
    def get_bloatware(self) -> Any:
        """Fetches the list of monitorable bloatware."""
        return self.BLOATWARE_PACKAGES

    def remove_bloatware(self, pkg_id: str) -> bool:
        """Surgically uninstalls UWP bloatware."""
        if not self.is_admin: return False
        ui_log(f"Removing Bloatware: {pkg_id}...", "CLEAN")
        try:
            cmd = f'powershell -Command "Get-AppxPackage -Name \'{pkg_id}\' -AllUsers | Remove-AppxPackage -AllUsers"'
            SystemUtils.execute(cmd, timeout=90)
            ui_log(f"Purged {pkg_id} successfully.", "CLEAN")
            return True
        except Exception as e:
            ui_log(f"Failed to purge {pkg_id}: {e}", "ERR", logging.ERROR)
            return False

    def reset_system(self) -> None:
        """Full Emergency Revert."""
        ui_log("EMERGENCY REVERT ENGAGED...", "UNDO", logging.WARNING)
        self.backup_manager.perform_rollback()
        ui_log("System restored to pre-optimized state.", "UNDO")

    # ------------------------------------------------------------------ #
    #  Advanced Process Priority Manager
    # ------------------------------------------------------------------ #

    def get_process_list(self) -> List[Dict[str, Any]]:
        """Delegate to SystemUtils for a live process snapshot.

        Returns:
            List of process dicts with name, pid, cpu, ram, priority, special.
        """
        return SystemUtils.get_process_list()

    def set_process_priority(self, pid: int, priority_key: str) -> bool:
        """Set the Windows priority class for a given PID.

        Args:
            pid:          Target process ID.
            priority_key: Priority level string ('realtime', 'high',
                          'above_normal', 'normal', 'below_normal', 'low').

        Returns:
            bool: True on success.
        """
        success = SystemUtils.set_process_priority(pid, priority_key)
        level_label = priority_key.replace("_", " ").title()
        if success:
            ui_log(f"PID {pid} → Priority set to [{level_label}]", "PROC")
        else:
            ui_log(f"Failed to set priority for PID {pid}.", "ERR", logging.WARNING)
        return success

    def boost_gaming_processes(self) -> int:
        """Elevate all detected gaming processes to HIGH priority.

        Returns:
            int: Number of processes successfully boosted.
        """
        ui_log("Boosting Gaming Processes → HIGH priority...", "PROC")
        count = self.boost_process_group(self.GAMING_PROCS)
        ui_log(f"{count} gaming process(es) priority-hardened.", "PROC")
        return count

    def boost_dev_processes_pm(self) -> int:
        """Elevate all detected development tool processes to HIGH priority.

        Returns:
            int: Number of processes successfully boosted.
        """
        ui_log("Boosting Dev Tool Processes → HIGH priority...", "PROC")
        count = self.boost_process_group(self.DEV_PROCS)
        ui_log(f"{count} development process(es) priority-hardened.", "PROC")
        return count

    def reset_all_priorities(self) -> int:
        """Reset ALL non-system processes to NORMAL priority.

        Returns:
            int: Number of processes successfully reset.
        """
        ui_log("Resetting ALL process priorities → NORMAL...", "PROC")
        count = 0
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info.get("name") or "").lower()
                # Skip core system processes to avoid instability
                if name in {"system", "registry", "smss.exe", "csrss.exe",
                            "wininit.exe", "services.exe", "lsass.exe"}:
                    continue
                pid = proc.info.get("pid", 0)
                if pid and SystemUtils.set_process_priority(pid, "normal"):
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception as exc:
                logger.debug("reset_all_priorities skip: %s", exc)
        ui_log(f"Priority reset complete. {count} process(es) normalized.", "PROC")
        return count

    # ------------------------------------------------------------------ #
    #  Privacy Shield
    # ------------------------------------------------------------------ #

    @staticmethod
    def _read_reg_dword(path: str, key: str) -> Optional[int]:
        """Read a single DWORD registry value. Returns None if missing."""
        import winreg
        _HIVE_MAP = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}
        parts = path.split("\\", 1)
        hive = _HIVE_MAP.get(parts[0])
        sub  = parts[1] if len(parts) > 1 else ""
        if not hive:
            return None
        try:
            with winreg.OpenKey(hive, sub, 0, winreg.KEY_READ) as k:
                val, _ = winreg.QueryValueEx(k, key)
                return int(val)
        except Exception:
            return None

    def get_privacy_status(self) -> List[Dict[str, Any]]:
        """Return PRIVACY_TWEAKS enriched with live registry 'active' state."""
        result = []
        for tweak in self.PRIVACY_TWEAKS:
            active = False
            if tweak["disable"]:
                first = tweak["disable"][0]
                current = self._read_reg_dword(first["path"], first["key"])
                if current is not None:
                    active = (str(current) == str(first["value"]))
            result.append({
                "id": tweak["id"], "name": tweak["name"],
                "category": tweak["category"], "risk": tweak["risk"],
                "desc": tweak["desc"], "active": active,
            })
        return result

    def apply_privacy_settings(self, enabled_ids: List[str],
                               progress_callback: Optional[Any] = None) -> Dict[str, Any]:
        """Apply/revert each privacy tweak. Creates backup first."""
        ui_log("Privacy Shield: Applying selected settings...", "PRIV")
        if progress_callback: progress_callback(10, "Creating Safety Backup")
        self.backup_manager.perform_full_backup()

        enabled_set = set(enabled_ids)
        applied = 0
        reverted = 0
        total = len(self.PRIVACY_TWEAKS)

        for i, tweak in enumerate(self.PRIVACY_TWEAKS):
            pct = 10 + int((i / total) * 85)
            if progress_callback:
                progress_callback(pct, f"Configuring: {tweak['name']}")
            ops = tweak["disable"] if tweak["id"] in enabled_set else tweak["enable"]
            for t in ops:
                SystemUtils.apply_registry_tweak(t)
            if tweak["id"] in enabled_set:
                applied += 1
                ui_log(f"[SHIELD] {tweak['name']} -> PRIVATE", "PRIV")
            else:
                reverted += 1
                ui_log(f"[SHIELD] {tweak['name']} -> DEFAULT", "PRIV")

        if progress_callback: progress_callback(100, "Privacy Shield Applied")
        ui_log(f"Privacy complete: {applied} private, {reverted} default.", "PRIV")
        return {"applied": applied, "reverted": reverted}

    def apply_privacy_profile(self, profile: str,
                              progress_callback: Optional[Any] = None) -> str:
        """Apply a named privacy profile: maximum | balanced | default."""
        ids = {
            "maximum":  self._PRIVACY_PROFILE_MAXIMUM,
            "balanced": self._PRIVACY_PROFILE_BALANCED,
            "default":  [],
        }.get(profile.lower(), [])
        ui_log(f"Privacy Profile: {profile.upper()} ({len(ids)} tweaks).", "PRIV")
        self.apply_privacy_settings(ids, progress_callback)
        return f"PROFILE_{profile.upper()}_APPLIED"
    # ------------------------------------------------------------------ #
    #  Advanced System Tweaks (Winaero Style)
    # ------------------------------------------------------------------ #

    def get_advanced_tweaks_status(self) -> List[Dict[str, Any]]:
        """Reads current registry values for all advanced tweaks."""
        results = []
        for tweak in RegistryVectors.ADVANCED_TWEAKS:
            active = False
            try:
                hive_str, path = tweak["path"].split("\\", 1)
                hive = getattr(winreg, f"HKEY_{hive_str}")
                with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
                    val, _ = winreg.QueryValueEx(key, tweak["key"])
                    # Check if value matches (string comparison for safety)
                    active = str(val).lower() == str(tweak["value"]).lower()
            except Exception:
                active = False
            
            tweak_copy = tweak.copy()
            tweak_copy["active"] = active
            results.append(tweak_copy)
        return results

    def apply_advanced_tweaks(self, tweak_ids: List[str]) -> bool:
        """Applies a batch of advanced registry tweaks."""
        if not self.is_admin: return False
        
        ui_log(f"Applying {len(tweak_ids)} Advanced Tweaks...", "TWK")
        self.backup_manager.perform_full_backup()
        
        success_count = 0
        for tweak in RegistryVectors.ADVANCED_TWEAKS:
            if tweak["id"] in tweak_ids:
                if SystemUtils.apply_registry_tweak(tweak):
                    success_count += 1
        
        ui_log(f"Successfully applied {success_count} tweaks.", "TWK")
        return True

    def reset_advanced_tweaks(self) -> bool:
        """Removes all advanced tweaks by restoring defaults (if possible) or deleting keys."""
        if not self.is_admin: return False
        ui_log("Resetting all Advanced Tweaks to Windows defaults...", "TWK", logging.WARNING)
        
        for tweak in RegistryVectors.ADVANCED_TWEAKS:
            # For most tweaks, we can just delete the value or set to 0
            # But safer to just delete if it was a 'positive' tweak
            SystemUtils.remove_registry_tweak(tweak["path"], tweak["key"])
            
        ui_log("Advanced tweaks reset complete. Explorer restart recommended.", "TWK")
        return True
    # ------------------------------------------------------------------ #
    #  Deep Cleaner Engine (BleachBit Style)
    # ------------------------------------------------------------------ #

    DEEP_CLEAN_CATEGORIES: List[Dict[str, Any]] = []  # Populated at runtime

    def _build_deep_clean_targets(self) -> List[Dict[str, Any]]:
        """Builds a comprehensive list of cleanable targets for every category."""
        user_local  = os.environ.get('LOCALAPPDATA', '')
        user_appdata = os.environ.get('APPDATA', '')
        user_home   = os.path.expanduser('~')
        windir      = os.environ.get('WINDIR', 'C:\\Windows')

        return [
            {
                "id": "system_temp",
                "name": "System Temp Files",
                "category": "System Cache",
                "icon": "🗂️",
                "paths": [
                    os.path.join(user_local, "Temp"),
                    os.path.join(windir, "Temp"),
                ],
            },
            {
                "id": "prefetch",
                "name": "Windows Prefetch",
                "category": "System Cache",
                "icon": "⚡",
                "paths": [os.path.join(windir, "Prefetch")],
            },
            {
                "id": "thumbnail_cache",
                "name": "Thumbnail Cache",
                "category": "System Cache",
                "icon": "🖼️",
                "paths": [
                    os.path.join(user_local, "Microsoft", "Windows", "Explorer"),
                ],
                "extensions": [".db"],
            },
            {
                "id": "win_update_cache",
                "name": "Windows Update Cache",
                "category": "System Cache",
                "icon": "🔄",
                "paths": [
                    os.path.join(windir, "SoftwareDistribution", "Download"),
                ],
            },
            {
                "id": "crash_dumps",
                "name": "Crash Dumps & Minidumps",
                "category": "System Cache",
                "icon": "💥",
                "paths": [
                    os.path.join(user_local, "CrashDumps"),
                    os.path.join(windir, "Minidump"),
                ],
            },
            {
                "id": "windows_logs",
                "name": "Windows Event Logs",
                "category": "Windows Logs",
                "icon": "📋",
                "paths": [
                    os.path.join(windir, "Logs"),
                    os.path.join(windir, "debug"),
                ],
                "extensions": [".log", ".etl"],
            },
            {
                "id": "chrome_cache",
                "name": "Google Chrome",
                "category": "Browser Caches",
                "icon": "🌐",
                "paths": [
                    os.path.join(user_local, "Google", "Chrome", "User Data", "Default", "Cache"),
                    os.path.join(user_local, "Google", "Chrome", "User Data", "Default", "Code Cache"),
                    os.path.join(user_local, "Google", "Chrome", "User Data", "Default", "GPUCache"),
                ],
            },
            {
                "id": "edge_cache",
                "name": "Microsoft Edge",
                "category": "Browser Caches",
                "icon": "🌐",
                "paths": [
                    os.path.join(user_local, "Microsoft", "Edge", "User Data", "Default", "Cache"),
                    os.path.join(user_local, "Microsoft", "Edge", "User Data", "Default", "Code Cache"),
                    os.path.join(user_local, "Microsoft", "Edge", "User Data", "Default", "GPUCache"),
                ],
            },
            {
                "id": "firefox_cache",
                "name": "Mozilla Firefox",
                "category": "Browser Caches",
                "icon": "🌐",
                "paths": [
                    os.path.join(user_appdata, "Mozilla", "Firefox", "Profiles"),
                ],
                "subdirs": ["cache2", "startupCache", "thumbnails"],
            },
            {
                "id": "recycle_bin",
                "name": "Recycle Bin",
                "category": "System Cache",
                "icon": "🗑️",
                "special": "recycle_bin",
            },
            {
                "id": "nvidia_shader",
                "name": "NVIDIA Shader Cache",
                "category": "GPU Caches",
                "icon": "🎮",
                "paths": [
                    os.path.join(user_local, "NVIDIA", "DXCache"),
                    os.path.join(user_local, "NVIDIA", "GLCache"),
                ],
            },
            {
                "id": "amd_shader",
                "name": "AMD Shader Cache",
                "category": "GPU Caches",
                "icon": "🎮",
                "paths": [
                    os.path.join(user_local, "AMD", "DxCache"),
                ],
            },
            {
                "id": "discord_cache",
                "name": "Discord",
                "category": "App Caches",
                "icon": "💬",
                "paths": [
                    os.path.join(user_appdata, "discord", "Cache"),
                    os.path.join(user_appdata, "discord", "Code Cache"),
                ],
            },
            {
                "id": "cursor_cache",
                "name": "Cursor IDE",
                "category": "App Caches",
                "icon": "🖊️",
                "paths": [
                    os.path.join(user_appdata, "Cursor", "Cache"),
                    os.path.join(user_appdata, "Cursor", "Code Cache"),
                ],
            },
            {
                "id": "vscode_cache",
                "name": "VS Code",
                "category": "App Caches",
                "icon": "💻",
                "paths": [
                    os.path.join(user_appdata, "Code", "Cache"),
                    os.path.join(user_appdata, "Code", "Code Cache"),
                    os.path.join(user_appdata, "Code", "logs"),
                ],
            },
            {
                "id": "steam_cache",
                "name": "Steam Webcache",
                "category": "App Caches",
                "icon": "🎮",
                "paths": [
                    os.path.join(user_local, "Steam", "htmlcache"),
                ],
            },
        ]

    def _get_dir_size(self, path: str, extensions: Optional[List[str]] = None,
                      subdirs: Optional[List[str]] = None) -> int:
        """Recursively calculates the size of a directory in bytes."""
        total = 0
        try:
            if subdirs:
                # Only scan specific sub-directory names within path
                for entry in os.scandir(path):
                    if entry.is_dir() and entry.name in subdirs:
                        total += self._get_dir_size(entry.path, extensions)
            else:
                for root, _, files in os.walk(path):
                    for f in files:
                        if extensions and not any(f.endswith(e) for e in extensions):
                            continue
                        try:
                            total += os.path.getsize(os.path.join(root, f))
                        except Exception:
                            pass
        except Exception:
            pass
        return total

    def _get_recycle_bin_size(self) -> int:
        """Estimates Recycle Bin size via SHGetDiskFreeSpaceEx approach."""
        total = 0
        try:
            import ctypes
            shell32 = ctypes.windll.shell32
            # Walk each drive's $Recycle.Bin
            for drive_letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                rb_path = f"{drive_letter}:\\$Recycle.Bin"
                if os.path.exists(rb_path):
                    total += self._get_dir_size(rb_path)
        except Exception:
            pass
        return total

    def analyze_deep_clean(self) -> List[Dict[str, Any]]:
        """Analyze all categories and return estimated space per category."""
        targets = self._build_deep_clean_targets()
        results = []

        for target in targets:
            size_bytes = 0
            exists = False

            if target.get("special") == "recycle_bin":
                size_bytes = self._get_recycle_bin_size()
                exists = True
            else:
                for p in target.get("paths", []):
                    if os.path.exists(p):
                        exists = True
                        size_bytes += self._get_dir_size(
                            p,
                            extensions=target.get("extensions"),
                            subdirs=target.get("subdirs")
                        )

            mb = round(size_bytes / (1024 * 1024), 1)
            results.append({
                "id": target["id"],
                "name": target["name"],
                "category": target["category"],
                "icon": target["icon"],
                "size_bytes": size_bytes,
                "size_mb": mb,
                "size_label": f"{mb} MB" if mb < 1024 else f"{round(mb/1024, 2)} GB",
                "exists": exists,
                "selected": mb > 0,
            })

        ui_log(f"Analysis complete. {len(results)} categories scanned.", "CLEAN")
        return results

    def run_deep_clean(self, category_ids: List[str],
                       progress_callback: Optional[Any] = None) -> Dict[str, Any]:
        """Execute cleaning for the specified category IDs. Returns results dict."""
        targets = {t["id"]: t for t in self._build_deep_clean_targets()}
        total = len(category_ids)
        freed_bytes = 0
        results = []

        for i, cat_id in enumerate(category_ids):
            target = targets.get(cat_id)
            if not target:
                continue

            if progress_callback:
                pct = int((i / total) * 95)
                progress_callback(pct, f"Cleaning: {target['name']}")

            cat_freed = 0

            if target.get("special") == "recycle_bin":
                try:
                    import ctypes
                    ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
                    cat_freed = 0  # Can't measure after cleaning
                except Exception:
                    pass
            else:
                for p in target.get("paths", []):
                    if not os.path.exists(p):
                        continue
                    scan_dirs = None
                    if target.get("subdirs"):
                        try:
                            scan_dirs = [
                                os.path.join(p, sd)
                                for sd in target["subdirs"]
                                if os.path.isdir(os.path.join(p, sd))
                            ]
                        except Exception:
                            scan_dirs = [p]
                    else:
                        scan_dirs = [p]

                    for scan_p in (scan_dirs or [p]):
                        try:
                            for root, dirs, files in os.walk(scan_p, topdown=False):
                                for f in files:
                                    ext = target.get("extensions")
                                    if ext and not any(f.endswith(e) for e in ext):
                                        continue
                                    try:
                                        fp = os.path.join(root, f)
                                        cat_freed += os.path.getsize(fp)
                                        os.remove(fp)
                                    except Exception:
                                        pass
                                for d in dirs:
                                    try:
                                        os.rmdir(os.path.join(root, d))
                                    except Exception:
                                        pass
                        except Exception as e:
                            logger.debug(f"DeepClean error [{cat_id}]: {e}")

            freed_bytes += cat_freed
            mb = round(cat_freed / (1024 * 1024), 1)
            results.append({
                "id": cat_id,
                "name": target["name"],
                "freed_mb": mb,
            })
            ui_log(f"Cleaned {target['name']}: {mb} MB freed.", "CLEAN")

        if progress_callback:
            progress_callback(100, "Deep Clean Complete")

        total_mb = round(freed_bytes / (1024 * 1024), 1)
        total_label = f"{total_mb} MB" if total_mb < 1024 else f"{round(total_mb/1024, 2)} GB"
        ui_log(f"🧹 Deep Clean finished. Total freed: {total_label}", "CLEAN")

        return {
            "freed_bytes": freed_bytes,
            "freed_mb": total_mb,
            "freed_label": total_label,
            "categories": results,
        }

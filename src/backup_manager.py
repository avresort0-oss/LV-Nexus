"""
backup_manager.py — Multi-Version Backup & Rollback System for LV Nexus v2.1.0
==================================================================================
Handles:
  - Timestamped registry exports (HKLM + HKCU separately)
  - Power plan exports (.pow)
  - Multi-version history with configurable retention
  - Selective rollback: choose ANY previous snapshot by index
  - Backup manifest (JSON) for integrity checking

Engineering Standards:
  - Full type hinting (PEP 484)
  - Comprehensive Google-style docstrings
  - Atomic operations where possible (write-then-rename)
  - Thread-safe (no shared mutable state beyond backup_dir)
"""

import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional

from .system_utils import SystemUtils

logger = logging.getLogger("LV_Nexus")

# Maximum number of versioned backup sets to retain on disk.
_MAX_BACKUP_VERSIONS: int = 10


def _ui_log(msg: str, tag: str = "SAFE", level: int = logging.INFO) -> None:
    """Emit a tagged log record that will be forwarded to the webview UI."""
    logger.log(level, msg, extra={"tag": tag})


class BackupManager:
    """Manages full, multi-version system backup and rollback.

    Each call to :meth:`perform_full_backup` creates a new *versioned backup
    set* inside ``backup_dir``.  A JSON manifest tracks all snapshots so the
    UI can display and restore any previous version.

    Directory layout::

        %LOCALAPPDATA%/LV_Nexus/Backups/
        ├── manifest.json                        # versioned index
        ├── 20260507_123456/                     # one set per backup
        │   ├── HKLM.reg
        │   ├── HKCU.reg
        │   └── powerplan.pow
        ├── 20260507_130000/
        │   └── …
        └── …

    Args:
        max_versions: Maximum number of backup sets to retain (FIFO eviction).
    """

    MANIFEST_FILE: str = "manifest.json"

    def __init__(self, max_versions: int = _MAX_BACKUP_VERSIONS) -> None:
        self.max_versions: int = max_versions
        self.backup_dir: Path = (
            Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LV_Nexus" / "Backups"
        )
        self.manifest_path: Path = self.backup_dir / self.MANIFEST_FILE

        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error("Cannot create backup directory [%s]: %s", self.backup_dir, exc)

        _ui_log(f"Backup directory ready: {self.backup_dir}", "SAFE")

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def perform_full_backup(self) -> bool:
        """Execute a full registry + power plan backup.

        Creates a new timestamped subdirectory and updates the manifest.
        Prunes old backup sets if the total exceeds ``max_versions``.

        Returns:
            bool: ``True`` if ALL steps succeeded; ``False`` if any step
                  failed (partial success is logged and noted in manifest).
        """
        _ui_log("Initiating Full System Backup Protocol …", "SAFE")
        ts = time.strftime("%Y%m%d_%H%M%S")
        set_dir = self.backup_dir / ts

        try:
            set_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _ui_log(f"Cannot create backup set directory: {exc}", "ERR", logging.ERROR)
            return False

        results: Dict[str, bool] = {}
        results["hklm_reg"] = self._backup_registry(set_dir, "HKLM")
        results["hkcu_reg"] = self._backup_registry(set_dir, "HKCU")
        results["power_plan"] = self._backup_power_plan(set_dir)

        overall_ok = all(results.values())
        self._update_manifest(ts, results, overall_ok)
        self._prune_old_backups()

        if overall_ok:
            _ui_log(f"Full Backup Completed Successfully → set: {ts}", "SAFE")
        else:
            failed = [k for k, v in results.items() if not v]
            _ui_log(
                f"Backup finished with warnings. Failed steps: {failed}",
                "ERR",
                logging.WARNING,
            )
        return overall_ok

    def perform_rollback(self, version_ts: Optional[str] = None) -> bool:
        """Restore system from a backup snapshot.

        Args:
            version_ts: Timestamp string of the backup set to restore
                        (e.g. ``"20260507_123456"``).  Defaults to the
                        **most recent** successful backup when ``None``.

        Returns:
            bool: ``True`` if rollback succeeded; ``False`` on failure.
        """
        _ui_log("Initiating System Rollback …", "UNDO")
        manifest = self._load_manifest()

        if version_ts is None:
            version_ts = self._find_latest_good_version(manifest)

        if version_ts is None:
            _ui_log("No valid backup snapshot found for rollback.", "ERR", logging.ERROR)
            return False

        set_dir = self.backup_dir / version_ts
        if not set_dir.exists():
            _ui_log(f"Backup set directory missing: {set_dir}", "ERR", logging.ERROR)
            return False

        _ui_log(f"Restoring from snapshot: {version_ts}", "UNDO")
        results: Dict[str, bool] = {}
        results["hklm_reg"] = self._restore_registry(set_dir, "HKLM")
        results["hkcu_reg"] = self._restore_registry(set_dir, "HKCU")
        results["power_plan"] = self._restore_power_plan(set_dir)

        overall_ok = all(results.values())
        if overall_ok:
            _ui_log("Full System Rollback Completed Successfully.", "UNDO")
        else:
            failed = [k for k, v in results.items() if not v]
            _ui_log(
                f"Rollback finished with warnings. Failed steps: {failed}",
                "ERR",
                logging.WARNING,
            )
        return overall_ok

    def list_backups(self) -> List[Dict[str, object]]:
        """Return a sorted list of backup snapshot metadata from the manifest.

        Returns:
            List[Dict]: Each entry contains ``'ts'``, ``'ok'``, and
                        ``'steps'`` keys — newest first.
        """
        manifest = self._load_manifest()
        versions = manifest.get("versions", [])
        return sorted(versions, key=lambda v: v.get("ts", ""), reverse=True)

    def get_backup_count(self) -> int:
        """Return the number of stored backup sets."""
        return len(self._load_manifest().get("versions", []))

    # ------------------------------------------------------------------ #
    #  Registry Backup / Restore
    # ------------------------------------------------------------------ #

    def _backup_registry(self, set_dir: Path, hive: str) -> bool:
        """Export a registry hive to ``set_dir``.

        Args:
            set_dir: Target backup set directory.
            hive:    ``"HKLM"`` or ``"HKCU"``.

        Returns:
            bool: ``True`` on success.
        """
        dest = set_dir / f"{hive}.reg"
        cmd = f'reg export {hive} "{dest}" /y'
        out = SystemUtils.execute(cmd, timeout=60)
        if out is None:
            _ui_log(f"Registry backup FAILED for {hive}.", "ERR", logging.ERROR)
            return False
        _ui_log(f"Registry snapshot saved: {dest.name}", "SAFE")
        return True

    def _restore_registry(self, set_dir: Path, hive: str) -> bool:
        """Import a registry hive from ``set_dir``.

        Args:
            set_dir: Backup set directory containing the ``.reg`` file.
            hive:    ``"HKLM"`` or ``"HKCU"``.

        Returns:
            bool: ``True`` on success.
        """
        src = set_dir / f"{hive}.reg"
        if not src.exists():
            _ui_log(f"Registry file not found: {src.name} — skipping.", "ERR", logging.WARNING)
            return False
        cmd = f'reg import "{src}"'
        out = SystemUtils.execute(cmd, timeout=60)
        if out is None:
            _ui_log(f"Registry restore FAILED for {hive}.", "ERR", logging.ERROR)
            return False
        _ui_log(f"Registry {hive} restored from: {src.name}", "UNDO")
        return True

    # ------------------------------------------------------------------ #
    #  Power Plan Backup / Restore
    # ------------------------------------------------------------------ #

    def _backup_power_plan(self, set_dir: Path) -> bool:
        """Export the active Windows power plan to ``set_dir``.

        Returns:
            bool: ``True`` on success.
        """
        guid = self._get_active_power_plan_guid()
        if not guid:
            _ui_log(
                "Cannot detect active power plan GUID — skipping power backup.",
                "ERR",
                logging.WARNING,
            )
            return False
        dest = set_dir / "powerplan.pow"
        out = SystemUtils.execute(f'powercfg -export "{dest}" {guid}', timeout=20)
        if out is None:
            _ui_log("Power plan backup FAILED.", "ERR", logging.ERROR)
            return False
        _ui_log(f"Power plan snapshot saved: {dest.name} (GUID={guid})", "SAFE")
        return True

    def _restore_power_plan(self, set_dir: Path) -> bool:
        """Import a power plan from ``set_dir`` and activate it.

        Falls back to the Windows *Balanced* plan if the file is missing.

        Returns:
            bool: ``True`` if the plan was successfully activated.
        """
        src = set_dir / "powerplan.pow"
        if not src.exists():
            _ui_log(
                "Power plan backup file missing — falling back to Balanced plan.",
                "ERR",
                logging.WARNING,
            )
            SystemUtils.execute("powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e")
            return False

        import_out = SystemUtils.execute(f'powercfg -import "{src}"', timeout=20)
        if import_out is None:
            _ui_log("Power plan import FAILED.", "ERR", logging.ERROR)
            # Fallback to balanced
            SystemUtils.execute("powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e")
            return False

        # Parse imported GUID from output: "Power Scheme GUID: <guid>  (<name>)"
        imported_guid = self._parse_guid_from_output(import_out)
        if imported_guid:
            SystemUtils.execute(f"powercfg /setactive {imported_guid}")
            _ui_log(f"Power plan restored and activated (GUID={imported_guid}).", "UNDO")
        else:
            _ui_log(
                "Power plan imported but GUID unparseable — activating Balanced.",
                "ERR",
                logging.WARNING,
            )
            SystemUtils.execute("powercfg /setactive 381b4222-f694-41f0-9685-ff5bb260df2e")
        return True

    # ------------------------------------------------------------------ #
    #  Manifest Management
    # ------------------------------------------------------------------ #

    def _load_manifest(self) -> Dict[str, object]:
        """Load and parse the backup manifest JSON.

        Returns:
            Dict with a ``'versions'`` list (empty if manifest is missing
            or corrupt).
        """
        if not self.manifest_path.exists():
            return {"versions": []}
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Manifest load failed (%s) — starting fresh.", exc)
            return {"versions": []}

    def _save_manifest(self, manifest: Dict[str, object]) -> None:
        """Atomically write the manifest to disk."""
        tmp = self.manifest_path.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(manifest, fh, indent=2)
            shutil.move(str(tmp), str(self.manifest_path))
        except OSError as exc:
            logger.error("Manifest save failed: %s", exc)

    def _update_manifest(self, ts: str, results: Dict[str, bool], overall_ok: bool) -> None:
        """Add a new backup entry to the manifest."""
        manifest = self._load_manifest()
        versions: List[Dict] = manifest.setdefault("versions", [])
        versions.append(
            {
                "ts": ts,
                "ok": overall_ok,
                "steps": results,
                "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        manifest["versions"] = versions
        self._save_manifest(manifest)

    def _prune_old_backups(self) -> None:
        """Remove oldest backup sets beyond ``max_versions``."""
        manifest = self._load_manifest()
        versions: List[Dict] = manifest.get("versions", [])
        if len(versions) <= self.max_versions:
            return

        versions_sorted = sorted(versions, key=lambda v: v.get("ts", ""))
        to_remove = versions_sorted[: len(versions) - self.max_versions]

        for entry in to_remove:
            ts = entry.get("ts", "")
            old_dir = self.backup_dir / ts
            try:
                if old_dir.exists():
                    shutil.rmtree(old_dir)
                    logger.info("Pruned old backup set: %s", ts)
            except OSError as exc:
                logger.warning("Could not prune backup set [%s]: %s", ts, exc)

        manifest["versions"] = versions_sorted[len(versions) - self.max_versions :]
        self._save_manifest(manifest)

    def _find_latest_good_version(self, manifest: Dict[str, object]) -> Optional[str]:
        """Return the timestamp of the most recent successful backup."""
        versions = sorted(
            manifest.get("versions", []),
            key=lambda v: v.get("ts", ""),
            reverse=True,
        )
        for v in versions:
            if v.get("ok"):
                return v["ts"]
        # Fallback: any version even if partially failed
        if versions:
            return versions[0]["ts"]
        return None

    # ------------------------------------------------------------------ #
    #  Power Plan Helpers
    # ------------------------------------------------------------------ #

    def _get_active_power_plan_guid(self) -> Optional[str]:
        """Retrieve the active Windows power plan GUID.

        Returns:
            Optional[str]: GUID string, or ``None`` if undetectable.
        """
        out = SystemUtils.execute("powercfg -getactivescheme", timeout=10)
        return self._parse_guid_from_output(out) if out else None

    @staticmethod
    def _parse_guid_from_output(text: Optional[str]) -> Optional[str]:
        """Extract a power plan GUID from ``powercfg`` output.

        Expected format: ``Power Scheme GUID: <guid>  (<name>)``

        Returns:
            Optional[str]: GUID on success, ``None`` otherwise.
        """
        if not text:
            return None
        parts = text.strip().split()
        for idx, part in enumerate(parts):
            if part.upper() == "GUID:" and idx + 1 < len(parts):
                candidate = parts[idx + 1].strip()
                # Basic GUID format validation
                if len(candidate) >= 32 and "-" in candidate:
                    return candidate
        return None

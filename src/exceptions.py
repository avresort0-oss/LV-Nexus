"""
exceptions.py — Custom Exception Hierarchy for LV Nexus v2.1.0
==============================================================

Defines a granular, structured exception hierarchy for the application.
This ensures that errors bubble up safely and can be displayed to the user
via the UI bridge with precise, human-readable messages.
"""


class LVNexusError(Exception):
    """Base exception for all LV Nexus specific errors."""
    def __init__(self, message: str = "An internal engine error occurred."):
        self.message = message
        super().__init__(self.message)


class ElevationRequiredError(LVNexusError):
    """Raised when an operation is attempted without Administrator privileges."""
    def __init__(self, message: str = "Administrator privileges are required for this action."):
        super().__init__(message)


class SystemExecutionError(LVNexusError):
    """Raised when a system subprocess (e.g., cmd, powershell) fails."""
    def __init__(self, command: str, detail: str = ""):
        msg = f"Failed to execute system command: '{command}'."
        if detail:
            msg += f" Details: {detail}"
        super().__init__(msg)


class RegistryAccessError(LVNexusError):
    """Raised when reading or writing to the Windows Registry fails."""
    def __init__(self, key: str, detail: str = ""):
        msg = f"Failed to modify registry key: {key}."
        if detail:
            msg += f" Details: {detail}"
        super().__init__(msg)


class BackupRestoreError(LVNexusError):
    """Raised during failures in system backup or rollback procedures."""
    def __init__(self, operation: str, detail: str = ""):
        msg = f"Backup subsystem failure during '{operation}'."
        if detail:
            msg += f" Details: {detail}"
        super().__init__(msg)


class OptimizationError(LVNexusError):
    """Raised during core engine optimization faults (e.g., thermal throttle blocks)."""
    def __init__(self, module: str, detail: str = ""):
        msg = f"Optimization module '{module}' encountered a fault."
        if detail:
            msg += f" Details: {detail}"
        super().__init__(msg)

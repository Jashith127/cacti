from __future__ import annotations

from enum import Enum

ACT_THRESHOLD = 0.85
CONFIRM_THRESHOLD = 0.50


class ExecutionTier(str, Enum):
    ACT = "act"
    CONFIRM = "confirm"
    REFUSE = "refuse"


class ToolRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


TOOL_RISK: dict[str, ToolRisk] = {
    "set_master_volume_percent": ToolRisk.LOW,
    "set_system_mute": ToolRisk.LOW,
    "set_default_audio_output": ToolRisk.HIGH,
    "focus_window": ToolRisk.LOW,
    "launch_application": ToolRisk.LOW,
    "snap_window": ToolRisk.MEDIUM,
    "get_foreground_window_title": ToolRisk.LOW,
    "get_active_browser_url": ToolRisk.LOW,
    "ocr_foreground_window": ToolRisk.HIGH,
    "credential_exists_for_target": ToolRisk.HIGH,
    "prompt_credential_for_target": ToolRisk.HIGH,
    "open_credential_manager_settings": ToolRisk.LOW,
    "refresh_app_registry": ToolRisk.MEDIUM,
    "list_matching_applications": ToolRisk.LOW,
}

# Tools that always require confirmation regardless of model confidence.
ALWAYS_CONFIRM: frozenset[str] = frozenset(
    {
        "set_default_audio_output",
        "ocr_foreground_window",
        "credential_exists_for_target",
        "prompt_credential_for_target",
    }
)

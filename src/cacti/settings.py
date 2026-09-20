from __future__ import annotations

from dataclasses import dataclass, field, asdict
import json
from pathlib import Path
from typing import Any

from cacti.apps.paths import default_cache_dir

TOOL_GROUPS: dict[str, tuple[str, ...]] = {
    "system": (
        "set_master_volume_percent",
        "set_system_mute",
        "set_default_audio_output",
    ),
    "windows": (
        "focus_window",
        "launch_application",
        "snap_window",
    ),
    "context": (
        "get_foreground_window_title",
        "get_active_browser_url",
        "ocr_foreground_window",
    ),
    "security": (
        "credential_exists_for_target",
        "prompt_credential_for_target",
        "open_credential_manager_settings",
    ),
    "apps": (
        "refresh_app_registry",
        "list_matching_applications",
    ),
}

GROUP_LABELS = {
    "system": "Volume, mute, and speakers",
    "windows": "Open, focus, and snap windows",
    "context": "Read window title, URL, and on-screen text",
    "security": "Windows Credential Manager (always asks)",
    "apps": "Search installed apps",
}

TOOL_LABELS = {
    "set_master_volume_percent": "Set volume",
    "set_system_mute": "Mute / unmute",
    "set_default_audio_output": "Switch speakers / headphones",
    "focus_window": "Focus a window",
    "launch_application": "Open an app",
    "snap_window": "Snap or maximize",
    "get_foreground_window_title": "Read the window title",
    "get_active_browser_url": "Read the browser URL",
    "ocr_foreground_window": "Read text on screen",
    "credential_exists_for_target": "Check saved logins",
    "prompt_credential_for_target": "Use a saved login",
    "open_credential_manager_settings": "Open Credential Manager",
    "refresh_app_registry": "Rescan installed apps",
    "list_matching_applications": "Search app names",
}

PTT_KEYS = ("f8", "f9", "f10", "rctrl", "ralt")


def default_tool_flags() -> dict[str, bool]:
    flags: dict[str, bool] = {}
    for names in TOOL_GROUPS.values():
        for name in names:
            flags[name] = True
    return flags


def default_settings_path() -> Path:
    return default_cache_dir() / "settings.json"


@dataclass
class CactiSettings:
    assistant_enabled: bool = True
    vad_enabled: bool = True
    ptt_enabled: bool = True
    ptt_key: str = "f8"
    stt_backend: str = "parakeet"
    asr_device: str = "auto"
    hide_after_turn: bool = True
    typed_commands: bool = True
    first_run_complete: bool = False
    vad_threshold: float = 0.018
    enabled_tools: dict[str, bool] = field(default_factory=default_tool_flags)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        tools = default_tool_flags()
        tools.update({k: bool(v) for k, v in self.enabled_tools.items() if k in tools})
        data["enabled_tools"] = tools
        return data

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> CactiSettings:
        tools = default_tool_flags()
        incoming = raw.get("enabled_tools") or {}
        if isinstance(incoming, dict):
            for key, value in incoming.items():
                if key in tools:
                    tools[key] = bool(value)
        ptt_key = str(raw.get("ptt_key", "f8")).lower()
        if ptt_key not in PTT_KEYS:
            ptt_key = "f8"
        stt = str(raw.get("stt_backend", "parakeet")).lower()
        if stt not in ("parakeet", "stub"):
            stt = "parakeet"
        device = str(raw.get("asr_device", "auto")).lower()
        if device not in ("auto", "cpu"):
            device = "auto"
        try:
            threshold = float(raw.get("vad_threshold", 0.018))
        except (TypeError, ValueError):
            threshold = 0.018
        threshold = min(0.08, max(0.006, threshold))
        return cls(
            assistant_enabled=bool(raw.get("assistant_enabled", True)),
            vad_enabled=bool(raw.get("vad_enabled", True)),
            ptt_enabled=bool(raw.get("ptt_enabled", True)),
            ptt_key=ptt_key,
            stt_backend=stt,
            asr_device=device,
            hide_after_turn=bool(raw.get("hide_after_turn", True)),
            typed_commands=bool(raw.get("typed_commands", True)),
            first_run_complete=bool(raw.get("first_run_complete", False)),
            vad_threshold=threshold,
            enabled_tools=tools,
        )

    def tool_enabled(self, name: str) -> bool:
        return bool(self.enabled_tools.get(name, True))

    def ptt_label(self) -> str:
        labels = {
            "f8": "F8",
            "f9": "F9",
            "f10": "F10",
            "rctrl": "Right Ctrl",
            "ralt": "Right Alt",
        }
        return labels.get(self.ptt_key, self.ptt_key.upper())


def load_settings(path: Path | None = None) -> CactiSettings:
    target = path or default_settings_path()
    if not target.is_file():
        return CactiSettings()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return CactiSettings()
        return CactiSettings.from_dict(raw)
    except (OSError, json.JSONDecodeError):
        return CactiSettings()


def save_settings(settings: CactiSettings, path: Path | None = None) -> Path:
    target = path or default_settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(settings.to_dict(), indent=2), encoding="utf-8")
    return target

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    confidence: float


def run_needle(transcript: str) -> list[ToolCall]:
    """
    Placeholder Needle 3 inference until the Cactus SDK is wired.
    Set CACTI_FAKE_TOOL='name:arg=value:confidence' or use simple prefixes.
    """
    import os

    fake = os.environ.get("CACTI_FAKE_TOOL", "").strip()
    if fake:
        return [_parse_fake_tool(fake)]

    text = transcript.strip().lower()
    if text.startswith("mute"):
        return [ToolCall("set_system_mute", {"muted": True}, 0.92)]
    if text.startswith("unmute"):
        return [ToolCall("set_system_mute", {"muted": False}, 0.92)]
    if "volume" in text:
        return [ToolCall("set_master_volume_percent", {"volume_percent": 50}, 0.9)]
    if text.startswith("focus "):
        title = transcript[6:].strip()
        return [ToolCall("focus_window", {"window_title": title}, 0.88)]
    if text.startswith("open "):
        app = transcript[5:].strip()
        return [ToolCall("launch_application", {"app_name": app}, 0.9)]
    return []


def _parse_fake_tool(spec: str) -> ToolCall:
    parts = spec.split(":")
    name = parts[0]
    args: dict[str, Any] = {}
    confidence = 0.9
    for part in parts[1:]:
        if part.startswith("confidence="):
            confidence = float(part.split("=", 1)[1])
        elif "=" in part:
            key, value = part.split("=", 1)
            if value.isdigit():
                args[key] = int(value)
            elif value in ("true", "false"):
                args[key] = value == "true"
            else:
                args[key] = value
    return ToolCall(name=name, arguments=args, confidence=confidence)

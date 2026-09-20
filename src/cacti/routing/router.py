from __future__ import annotations

from typing import Any

from cacti.routing.tiers import (
    ACT_THRESHOLD,
    ALWAYS_CONFIRM,
    CONFIRM_THRESHOLD,
    TOOL_RISK,
    ExecutionTier,
    ToolRisk,
)


def _volume_requires_confirm(args: dict[str, Any]) -> bool:
    raw = args.get("volume_percent")
    if raw is None:
        return False
    try:
        level = int(raw)
    except (TypeError, ValueError):
        return True
    return level <= 10 or level >= 100


def route_tool_turn(
    tool_name: str,
    args: dict[str, Any],
    confidence: float,
) -> ExecutionTier:
    """Map Needle confidence + tool risk to act, confirm, or refuse."""
    if confidence < CONFIRM_THRESHOLD:
        return ExecutionTier.REFUSE

    if tool_name not in TOOL_RISK:
        return ExecutionTier.REFUSE

    if tool_name in ALWAYS_CONFIRM:
        return ExecutionTier.CONFIRM

    if tool_name == "set_master_volume_percent" and _volume_requires_confirm(args):
        return ExecutionTier.CONFIRM

    risk = TOOL_RISK[tool_name]
    if risk in (ToolRisk.MEDIUM, ToolRisk.HIGH):
        if confidence >= ACT_THRESHOLD and risk == ToolRisk.MEDIUM:
            return ExecutionTier.CONFIRM
        return ExecutionTier.CONFIRM

    if confidence >= ACT_THRESHOLD:
        return ExecutionTier.ACT
    return ExecutionTier.CONFIRM

from __future__ import annotations

from cacti.routing.router import route_tool_turn
from cacti.routing.tiers import ExecutionTier


def test_refuse_low_confidence():
    assert route_tool_turn("set_system_mute", {"muted": True}, 0.4) == ExecutionTier.REFUSE


def test_act_high_confidence_low_risk():
    assert (
        route_tool_turn("set_system_mute", {"muted": True}, 0.9) == ExecutionTier.ACT
    )


def test_confirm_default_audio_always():
    assert (
        route_tool_turn("set_default_audio_output", {"device_name": "headphones"}, 0.99)
        == ExecutionTier.CONFIRM
    )


def test_confirm_extreme_volume():
    assert (
        route_tool_turn("set_master_volume_percent", {"volume_percent": 0}, 0.95)
        == ExecutionTier.CONFIRM
    )
    assert (
        route_tool_turn("set_master_volume_percent", {"volume_percent": 50}, 0.95)
        == ExecutionTier.ACT
    )


def test_unmapped_tool_refused():
    assert route_tool_turn("nonexistent_tool", {}, 0.99) == ExecutionTier.REFUSE


def test_needle_registry_has_twelve_core_tools():
    from cacti.needle_registry import ALL_TOOLS

    names = {fn.__name__ for fn in ALL_TOOLS}
    core = {
        "set_master_volume_percent",
        "set_system_mute",
        "set_default_audio_output",
        "focus_window",
        "launch_application",
        "snap_window",
        "get_foreground_window_title",
        "get_active_browser_url",
        "ocr_foreground_window",
        "credential_exists_for_target",
        "prompt_credential_for_target",
        "open_credential_manager_settings",
    }
    assert core.issubset(names)

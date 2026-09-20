from __future__ import annotations

from unittest.mock import patch

from cacti.assistant.loop import run_once


def test_run_once_refuses_low_confidence(monkeypatch):
    monkeypatch.setenv(
        "CACTI_FAKE_TOOL",
        "set_default_audio_output:device_name=speakers:confidence=0.4",
    )
    with patch("cacti.assistant.engine.startup"):
        with patch("builtins.input", return_value="yes"):
            out = run_once(transcript="ignored")
    assert out == ["refused"]


def test_run_once_mute_act(monkeypatch):
    monkeypatch.setenv("CACTI_FAKE_TOOL", "set_system_mute:muted=true:confidence=0.95")
    with patch("cacti.assistant.engine.startup"):
        with patch(
            "cacti.assistant.engine.TOOL_BY_NAME",
            {"set_system_mute": lambda muted: "Muted."},
        ):
            out = run_once(transcript="mute")
    assert out == ["Muted."]

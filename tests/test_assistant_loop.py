from __future__ import annotations

import os
from unittest.mock import patch

from cacti.assistant.loop import run_once


def test_run_once_refuses_low_confidence(monkeypatch):
    monkeypatch.setenv("CACTI_FAKE_TOOL", "set_default_audio_output:device_name=speakers:confidence=0.4")
    with patch("cacti.assistant.loop.startup"):
        with patch("builtins.input", return_value="yes"):
            out = run_once(transcript="ignored")
    assert out == ["refused"]


def test_run_once_mute_act(monkeypatch):
    monkeypatch.setenv("CACTI_FAKE_TOOL", "set_system_mute:muted=true:confidence=0.95")
    with patch("cacti.assistant.loop.startup"):
        with patch("cacti.tools.system_hardware.set_system_mute", return_value="Muted."):
            out = run_once(transcript="mute")
    assert "Muted." in out[0] or "error" in out[0]

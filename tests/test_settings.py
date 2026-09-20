from __future__ import annotations

from cacti.settings import CactiSettings, load_settings, save_settings


def test_settings_round_trip(tmp_path):
    path = tmp_path / "settings.json"
    settings = CactiSettings(assistant_enabled=False, ptt_key="f9", stt_backend="stub")
    settings.enabled_tools["ocr_foreground_window"] = False
    save_settings(settings, path)
    loaded = load_settings(path)
    assert loaded.assistant_enabled is False
    assert loaded.ptt_key == "f9"
    assert loaded.stt_backend == "stub"
    assert loaded.tool_enabled("ocr_foreground_window") is False
    assert loaded.tool_enabled("set_system_mute") is True


def test_invalid_ptt_key_falls_back():
    loaded = CactiSettings.from_dict({"ptt_key": "left-mouse"})
    assert loaded.ptt_key == "f8"


def test_engine_respects_disabled_tool(monkeypatch):
    from cacti.assistant.engine import AssistantEngine

    monkeypatch.setenv("CACTI_FAKE_TOOL", "set_system_mute:muted=true:confidence=0.95")
    engine = AssistantEngine(tool_allowed=lambda _name: False)
    engine._started = True
    assert engine.handle_transcript("mute") == ["disabled"]

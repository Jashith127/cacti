from __future__ import annotations

from cacti.assistant.engine import AssistantEngine


def test_engine_refuses_low_confidence(monkeypatch):
    monkeypatch.setenv(
        "CACTI_FAKE_TOOL",
        "set_default_audio_output:device_name=speakers:confidence=0.4",
    )
    events = []
    engine = AssistantEngine(
        on_event=events.append,
        confirm=lambda _c: True,
    )
    engine._started = True
    out = engine.handle_transcript("ignored")
    assert out == ["refused"]
    assert any(e.kind == "refuse" for e in events)


def test_engine_act_mute(monkeypatch):
    monkeypatch.setenv("CACTI_FAKE_TOOL", "set_system_mute:muted=true:confidence=0.95")
    from unittest.mock import patch

    engine = AssistantEngine(confirm=lambda _c: True)
    engine._started = True
    with patch("cacti.assistant.engine.TOOL_BY_NAME", {"set_system_mute": lambda muted: "Muted."}):
        out = engine.handle_transcript("mute")
    assert out == ["Muted."]


def test_engine_confirm_can_cancel(monkeypatch):
    monkeypatch.setenv(
        "CACTI_FAKE_TOOL",
        "ocr_foreground_window:confidence=0.95",
    )
    engine = AssistantEngine(confirm=lambda _c: False)
    engine._started = True
    out = engine.handle_transcript("read the screen")
    assert out == ["cancelled"]


def test_stt_factory_default_is_stub(monkeypatch):
    from cacti.assistant.stt.factory import get_stt_provider
    from cacti.assistant.stt_stub import StubSTTProvider
    from cacti.settings import CactiSettings

    assert isinstance(get_stt_provider(settings=CactiSettings(stt_backend="stub")), StubSTTProvider)


def test_stt_factory_parakeet(monkeypatch):
    from cacti.assistant.stt.factory import get_stt_provider
    from cacti.assistant.stt.parakeet import ParakeetSTTProvider
    from cacti.settings import CactiSettings

    assert isinstance(
        get_stt_provider(settings=CactiSettings(stt_backend="parakeet")),
        ParakeetSTTProvider,
    )

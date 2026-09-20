from __future__ import annotations

import os

from cacti.assistant.stt_stub import STTProvider, StubSTTProvider


def get_stt_provider(name: str | None = None) -> STTProvider:
    """Pick STT backend: stub (default) or parakeet (NVIDIA Parakeet TDT 0.6B v2 ONNX)."""
    chosen = (name or os.environ.get("CACTI_STT", "stub")).strip().lower()
    if chosen in ("parakeet", "parakeet-v2", "nemo-parakeet"):
        from cacti.assistant.stt.parakeet import ParakeetSTTProvider

        return ParakeetSTTProvider()
    return StubSTTProvider()

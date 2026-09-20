from __future__ import annotations

from cacti.assistant.stt.onnx_runtime import prefer_gpu_providers
from cacti.assistant.stt_stub import STTProvider, StubSTTProvider
from cacti.settings import CactiSettings, load_settings


def get_stt_provider(
    name: str | None = None,
    *,
    settings: CactiSettings | None = None,
) -> STTProvider:
    cfg = settings or load_settings()
    chosen = (name or cfg.stt_backend or "parakeet").strip().lower()
    if chosen in ("parakeet", "parakeet-v2", "nemo-parakeet"):
        from cacti.assistant.stt.parakeet import ParakeetSTTProvider

        runtime = prefer_gpu_providers(force_cpu=cfg.asr_device == "cpu")
        return ParakeetSTTProvider(runtime=runtime)
    return StubSTTProvider()

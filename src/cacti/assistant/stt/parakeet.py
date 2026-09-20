from __future__ import annotations

from pathlib import Path

from cacti.assistant.stt.onnx_runtime import OnnxRuntimeChoice, prefer_gpu_providers
from cacti.assistant.stt_stub import STTProvider
from cacti.errors import PlatformUnsupported

PARAKEET_MODEL = "nemo-parakeet-tdt-0.6b-v2"


class ParakeetSTTProvider(STTProvider):
    """
    Local NVIDIA Parakeet TDT 0.6B v2 via onnx-asr.

    Prefers CUDAExecutionProvider when onnxruntime-gpu is installed and a GPU is
    visible, then DirectML, then CPU. Falls back to CPU if GPU session creation fails.
    """

    def __init__(
        self,
        model_name: str = PARAKEET_MODEL,
        runtime: OnnxRuntimeChoice | None = None,
    ) -> None:
        self.model_name = model_name
        self.runtime = runtime or prefer_gpu_providers()
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        try:
            import onnx_asr
        except ImportError as exc:
            raise PlatformUnsupported(
                "Parakeet STT needs onnx-asr (pip install -e '.[asr]' or '.[asr-cuda]')."
            ) from exc

        providers = list(self.runtime.providers)
        try:
            self._model = onnx_asr.load_model(self.model_name, providers=providers)
        except Exception:
            self._model = onnx_asr.load_model(
                self.model_name, providers=["CPUExecutionProvider"]
            )
        return self._model

    def transcribe(self, audio_path: Path | None = None) -> str:
        if audio_path is None or not audio_path.is_file():
            return ""
        return self._normalize(self._ensure_model().recognize(str(audio_path)))

    def transcribe_samples(self, samples, sample_rate: int = 16000) -> str:
        import numpy as np

        waveform = np.asarray(samples, dtype=np.float32).reshape(-1)
        if waveform.size == 0:
            return ""
        model = self._ensure_model()
        result = model.recognize(waveform, sample_rate=int(sample_rate))
        return self._normalize(result)

    @staticmethod
    def _normalize(result) -> str:
        text = getattr(result, "text", None)
        if text:
            return str(text).strip()
        if isinstance(result, list):
            parts = []
            for part in result:
                parts.append(str(getattr(part, "text", part) or "").strip())
            return " ".join(p for p in parts if p)
        return str(result or "").strip()

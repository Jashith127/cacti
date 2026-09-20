from __future__ import annotations

import os
import wave
from abc import ABC, abstractmethod
from pathlib import Path


class STTProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path | None = None) -> str:
        ...


class StubSTTProvider(STTProvider):
    """Development STT: env utterance or optional 16-bit mono WAV."""

    def transcribe(self, audio_path: Path | None = None) -> str:
        env = os.environ.get("CACTI_TEST_UTTERANCE", "").strip()
        if env:
            return env
        if audio_path and audio_path.is_file():
            return self._transcribe_wav_placeholder(audio_path)
        return ""


    def _transcribe_wav_placeholder(self, audio_path: Path) -> str:
        with wave.open(str(audio_path), "rb") as wf:
            if wf.getnframes() == 0:
                return ""
        return os.environ.get("CACTI_TEST_UTTERANCE", "[audio received]")

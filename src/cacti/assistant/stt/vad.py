from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EnergyVAD:
    """Simple RMS voice-activity detector. Does not run ASR — only gates capture."""

    sample_rate: int = 16000
    threshold: float = 0.018
    start_frames: int = 4
    hangover_frames: int = 12
    _speech_frames: int = 0
    _silence_frames: int = 0
    speaking: bool = False

    def rms(self, samples: list[float] | tuple[float, ...]) -> float:
        if not samples:
            return 0.0
        acc = 0.0
        for value in samples:
            acc += value * value
        return (acc / len(samples)) ** 0.5

    def feed(self, samples: list[float] | tuple[float, ...]) -> str | None:
        """
        Ingest one audio block.
        Returns 'start' on speech onset, 'end' after hangover silence, else None.
        """
        level = self.rms(samples)
        if level >= self.threshold:
            self._speech_frames += 1
            self._silence_frames = 0
            if not self.speaking and self._speech_frames >= self.start_frames:
                self.speaking = True
                return "start"
            return None

        self._speech_frames = 0
        if not self.speaking:
            return None
        self._silence_frames += 1
        if self._silence_frames >= self.hangover_frames:
            self.speaking = False
            self._silence_frames = 0
            return "end"
        return None

    def reset(self) -> None:
        self._speech_frames = 0
        self._silence_frames = 0
        self.speaking = False

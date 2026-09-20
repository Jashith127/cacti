from __future__ import annotations

from cacti.errors import PlatformUnsupported


def record_seconds(seconds: float = 4.0, sample_rate: int = 16000):
    """Capture mono float32 PCM from the default microphone."""
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as exc:
        raise PlatformUnsupported(
            "Microphone capture needs sounddevice and numpy (pip install -e '.[asr]')."
        ) from exc

    frames = int(seconds * sample_rate)
    audio = sd.rec(frames, samplerate=sample_rate, channels=1, dtype="float32")
    sd.wait()
    return np.squeeze(audio), sample_rate

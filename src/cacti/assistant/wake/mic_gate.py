from __future__ import annotations

import threading
from collections.abc import Callable

from cacti.assistant.stt.vad import EnergyVAD
from cacti.errors import PlatformUnsupported

UtteranceFn = Callable[[list[float], int], None]
StateFn = Callable[[str], None]


class MicGate:
    """Background mic: VAD onset/offset or push-to-talk hold. Hidden UI until speech."""

    def __init__(
        self,
        *,
        on_utterance: UtteranceFn,
        on_state: StateFn | None = None,
        sample_rate: int = 16000,
        vad: bool = True,
    ) -> None:
        self._on_utterance = on_utterance
        self._on_state = on_state or (lambda _s: None)
        self.sample_rate = sample_rate
        self.vad_enabled = vad
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._buffer: list[float] = []
        self._capturing = False
        self._ptt = False
        self._stream = None
        self._thread: threading.Thread | None = None
        self._vad = EnergyVAD(sample_rate=sample_rate)

    def start(self) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise PlatformUnsupported(
                "Wake listening needs sounddevice (pip install -e '.[asr]')."
            ) from exc

        self._stop.clear()
        block = int(self.sample_rate * 0.03)

        def callback(indata, _frames, _time, status) -> None:
            if status or self._stop.is_set():
                return
            samples = [float(x[0]) for x in indata]
            self._on_block(samples)

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=block,
            callback=callback,
        )
        self._stream.start()

    def stop(self) -> None:
        self._stop.set()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def ptt_down(self) -> None:
        with self._lock:
            self._ptt = True
            self._capturing = True
            self._buffer = []
            self._vad.reset()
        self._on_state("ptt")

    def ptt_up(self) -> None:
        utterance: list[float] = []
        with self._lock:
            self._ptt = False
            if self._capturing:
                utterance = self._buffer
            self._capturing = False
            self._buffer = []
        if utterance:
            self._on_utterance(utterance, self.sample_rate)

    def _on_block(self, samples: list[float]) -> None:
        started = False
        utterance: list[float] | None = None
        with self._lock:
            if self._ptt:
                self._buffer.extend(samples)
                return
            if not self.vad_enabled:
                return
            event = self._vad.feed(samples)
            if event == "start":
                self._capturing = True
                self._buffer = list(samples)
                started = True
            elif self._capturing:
                self._buffer.extend(samples)
                if event == "end":
                    utterance = self._buffer
                    self._capturing = False
                    self._buffer = []
        if started:
            self._on_state("vad")
        if utterance:
            self._on_utterance(utterance, self.sample_rate)

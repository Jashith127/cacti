from __future__ import annotations

import sys


class TTSProvider:
    def speak(self, text: str) -> None:
        if not text:
            return
        print(f"TTS: {text}", file=sys.stderr)

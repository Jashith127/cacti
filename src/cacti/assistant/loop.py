from __future__ import annotations

import argparse
from pathlib import Path

from cacti.assistant.engine import AssistantEngine
from cacti.assistant.stt.factory import get_stt_provider
from cacti.assistant.tts_stub import TTSProvider


def run_once(transcript: str | None = None, audio: Path | None = None) -> list[str]:
    tts = TTSProvider()
    engine = AssistantEngine(
        speak=tts.speak,
        confirm=lambda _call: input("confirm [yes/no]: ").strip().lower() in ("yes", "y", "confirm"),
    )
    if transcript is None:
        transcript = get_stt_provider().transcribe(audio)
    return engine.handle_transcript(transcript)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cacti assistant loop (dev stub)")
    parser.add_argument("--text", help="Bypass STT with fixed transcript")
    parser.add_argument("--wav", type=Path, help="Optional WAV for STT")
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Run hidden until VAD or F8 push-to-talk",
    )
    args = parser.parse_args(argv)

    if args.ui:
        from cacti.ui.app import run_ui

        run_ui()
        return 0

    outputs = run_once(transcript=args.text, audio=args.wav)
    for line in outputs:
        print(line)
    return 0 if outputs else 1


if __name__ == "__main__":
    raise SystemExit(main())

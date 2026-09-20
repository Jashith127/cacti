from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cacti.assistant.bootstrap import startup
from cacti.assistant.needle_client import ToolCall, run_needle
from cacti.assistant.stt_stub import StubSTTProvider
from cacti.assistant.tts_stub import TTSProvider
from cacti.errors import CactiError
from cacti.needle_registry import TOOL_BY_NAME
from cacti.routing.router import route_tool_turn
from cacti.routing.tiers import ExecutionTier


def _confirm(tts: TTSProvider, call: ToolCall) -> bool:
    tts.speak(f"Confirm {call.name} with {call.arguments}? Say yes or no.")
    answer = input("confirm [yes/no]: ").strip().lower()
    return answer in ("yes", "y", "confirm")


def execute_call(call: ToolCall, tts: TTSProvider) -> str:
    tier = route_tool_turn(call.name, call.arguments, call.confidence)
    if tier == ExecutionTier.REFUSE:
        tts.speak("I cannot do that safely.")
        return "refused"

    if tier == ExecutionTier.CONFIRM and not _confirm(tts, call):
        tts.speak("Cancelled.")
        return "cancelled"

    fn = TOOL_BY_NAME.get(call.name)
    if fn is None:
        tts.speak("Tool not registered.")
        return "unmapped"

    try:
        result = fn(**call.arguments)
        return str(result)
    except CactiError as exc:
        tts.speak(exc.message)
        return f"error: {exc.message}"
    except Exception as exc:
        tts.speak("Something went wrong.")
        return f"error: {exc}"


def run_once(transcript: str | None = None, audio: Path | None = None) -> list[str]:
    startup()
    stt = StubSTTProvider()
    tts = TTSProvider()
    text = transcript if transcript is not None else stt.transcribe(audio)
    if not text.strip():
        tts.speak("I did not hear anything.")
        return []

    calls = run_needle(text)
    if not calls:
        tts.speak("No matching action.")
        return []

    return [execute_call(call, tts) for call in calls]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cacti assistant loop (dev stub)")
    parser.add_argument("--text", help="Bypass STT with fixed transcript")
    parser.add_argument("--wav", type=Path, help="Optional WAV for STT stub")
    args = parser.parse_args(argv)

    outputs = run_once(transcript=args.text, audio=args.wav)
    for line in outputs:
        print(line)
    return 0 if outputs else 1


if __name__ == "__main__":
    raise SystemExit(main())

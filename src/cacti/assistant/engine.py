from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from cacti.assistant.bootstrap import startup
from cacti.assistant.needle_client import ToolCall, run_needle
from cacti.errors import CactiError
from cacti.needle_registry import TOOL_BY_NAME
from cacti.routing.router import route_tool_turn
from cacti.routing.tiers import ExecutionTier


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    CONFIRM = "confirm"
    SPEAKING = "speaking"
    DONE = "done"


@dataclass(frozen=True)
class AssistantEvent:
    kind: str
    state: AssistantState
    text: str = ""
    payload: dict[str, Any] | None = None


ConfirmFn = Callable[[ToolCall], bool]
SpeakFn = Callable[[str], None]
EventFn = Callable[[AssistantEvent], None]


class AssistantEngine:
    """Shared turn pipeline used by the CLI and the floating UI."""

    def __init__(
        self,
        *,
        speak: SpeakFn | None = None,
        on_event: EventFn | None = None,
        confirm: ConfirmFn | None = None,
    ) -> None:
        self._speak = speak or (lambda _text: None)
        self._on_event = on_event or (lambda _event: None)
        self._confirm = confirm
        self._started = False

    def ensure_started(self) -> None:
        if not self._started:
            startup()
            self._started = True

    def _emit(self, kind: str, state: AssistantState, text: str = "", **payload: Any) -> None:
        event = AssistantEvent(kind=kind, state=state, text=text, payload=payload or None)
        self._on_event(event)
        if text and kind in {"speak", "refuse", "error"}:
            self._speak(text)

    def handle_transcript(self, transcript: str) -> list[str]:
        self.ensure_started()
        text = transcript.strip()
        if not text:
            self._emit("speak", AssistantState.IDLE, "I did not hear anything.")
            return []

        self._emit("heard", AssistantState.THINKING, text)
        calls = run_needle(text)
        if not calls:
            self._emit("speak", AssistantState.IDLE, "No matching action.")
            return []

        results: list[str] = []
        for call in calls:
            results.append(self._execute(call))
        last = results[-1] if results else ""
        self._emit("done", AssistantState.DONE, last)
        return results

    def _execute(self, call: ToolCall) -> str:
        tier = route_tool_turn(call.name, call.arguments, call.confidence)
        if tier == ExecutionTier.REFUSE:
            self._emit("refuse", AssistantState.IDLE, "I cannot do that safely.")
            return "refused"

        if tier == ExecutionTier.CONFIRM:
            self._emit(
                "confirm",
                AssistantState.CONFIRM,
                f"Do {call.name.replace('_', ' ')}?",
                tool=call.name,
                arguments=call.arguments,
            )
            if self._confirm is None or not self._confirm(call):
                self._emit("speak", AssistantState.IDLE, "Cancelled.")
                return "cancelled"

        fn = TOOL_BY_NAME.get(call.name)
        if fn is None:
            self._emit("error", AssistantState.IDLE, "Tool not registered.")
            return "unmapped"

        try:
            result = str(fn(**call.arguments))
            self._emit("result", AssistantState.DONE, result, tool=call.name)
            return result
        except CactiError as exc:
            self._emit("error", AssistantState.IDLE, exc.message)
            return f"error: {exc.message}"
        except Exception:
            self._emit("error", AssistantState.IDLE, "Something went wrong.")
            return "error: Something went wrong."

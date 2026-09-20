from __future__ import annotations

import math
import os
import threading
import tkinter as tk
from tkinter import font as tkfont

from cacti.assistant.engine import AssistantEngine, AssistantEvent, AssistantState
from cacti.assistant.needle_client import ToolCall
from cacti.assistant.stt.factory import get_stt_provider
from cacti.assistant.stt.parakeet import ParakeetSTTProvider
from cacti.assistant.wake.hotkey import PushToTalkHotkey
from cacti.assistant.wake.mic_gate import MicGate
from cacti.errors import PlatformUnsupported

SAND = "#F4EDE4"
MOSS = "#3F5D4A"
MOSS_SOFT = "#6B8F78"
INK = "#2C2A26"
MIST = "#E7DDD1"
CREAM = "#FFF8F0"
PULSE = "#9BB8A4"

HIDE_AFTER_MS = 2800


class FuzzyOrb(tk.Tk):
    """Hidden until VAD or push-to-talk (F8). Then a small fuzzy pebble appears."""

    def __init__(self) -> None:
        super().__init__()
        self.title("cacti")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.97)
        except tk.TclError:
            pass
        self.configure(bg=SAND)
        self.withdraw()

        self._engine = AssistantEngine(
            speak=self._speak_later,
            on_event=self._on_engine_event,
            confirm=self._wait_for_confirm,
        )
        self._stt = get_stt_provider()
        self._confirm_event = threading.Event()
        self._confirm_yes = False
        self._busy = False
        self._awaiting_confirm = False
        self._phase = 0.0
        self._drag = (0, 0)
        self._hide_job: str | None = None
        self._gate: MicGate | None = None
        self._hotkey: PushToTalkHotkey | None = None

        self._build()
        self.after(40, self._animate)
        self.after(80, self._place_corner)
        self.after(120, self._start_wake)
        self.protocol("WM_DELETE_WINDOW", self._quit)

    def _build(self) -> None:
        self.card = tk.Frame(self, bg=SAND, bd=0, highlightthickness=0)
        self.card.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(
            self.card, width=88, height=88, bg=SAND, highlightthickness=0, bd=0
        )
        self.canvas.pack(side="left", padx=(4, 8), pady=4)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonPress-1>", self._start_drag)

        body = tk.Frame(self.card, bg=SAND)
        body.pack(side="left", fill="both", expand=True, pady=6)

        title_font = tkfont.Font(family="Georgia", size=16, slant="italic")
        tk.Label(body, text="cacti", fg=MOSS, bg=SAND, font=title_font, anchor="w").pack(
            fill="x"
        )

        self.status = tk.Label(
            body,
            text="listening for you",
            fg=MOSS_SOFT,
            bg=SAND,
            font=("Segoe UI", 10),
            anchor="w",
        )
        self.status.pack(fill="x")

        self.transcript = tk.Label(
            body,
            text="",
            fg=INK,
            bg=SAND,
            font=("Segoe UI", 11),
            wraplength=260,
            justify="left",
            anchor="w",
        )
        self.transcript.pack(fill="x", pady=(6, 4))

        self.confirm_row = tk.Frame(body, bg=SAND)
        tk.Button(
            self.confirm_row,
            text="yes",
            command=lambda: self._resolve_confirm(True),
            bg=MOSS,
            fg=CREAM,
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
        ).pack(side="left")
        tk.Button(
            self.confirm_row,
            text="not now",
            command=lambda: self._resolve_confirm(False),
            bg=MIST,
            fg=INK,
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))

        hint = tk.Label(
            body,
            text="hold F8 to talk · speak to wake · Esc dismisses",
            fg=MOSS_SOFT,
            bg=SAND,
            font=("Segoe UI", 8),
            anchor="w",
        )
        hint.pack(fill="x", pady=(8, 0))

        self.bind("<Escape>", lambda _e: self._hide())
        self._draw_orb(0.0)

    def _place_corner(self) -> None:
        self.update_idletasks()
        w, h = 420, 160
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{sw - w - 28}+{sh - h - 72}")

    def _start_wake(self) -> None:
        modes = os.environ.get("CACTI_WAKE", "vad,ptt").lower()
        want_vad = "vad" in modes
        want_ptt = "ptt" in modes
        try:
            self._gate = MicGate(
                on_utterance=self._on_utterance,
                on_state=lambda kind: self.after(
                    0, lambda k=kind: self._show_listening(k)
                ),
                vad=want_vad,
            )
            self._gate.start()
        except PlatformUnsupported as exc:
            self._set_status(exc.message)

        if want_ptt:
            try:
                self._hotkey = PushToTalkHotkey(
                    on_down=lambda: self.after(0, self._ptt_down),
                    on_up=lambda: self.after(0, self._ptt_up),
                )
                self._hotkey.start()
            except PlatformUnsupported:
                pass

    def _show_listening(self, kind: str) -> None:
        self._cancel_hide()
        self.deiconify()
        self.lift()
        label = "hold F8…" if kind == "ptt" else "heard you…"
        self._set_status(label)
        self.transcript.configure(text="")

    def _ptt_down(self) -> None:
        if self._gate is None:
            return
        self._show_listening("ptt")
        self._gate.ptt_down()

    def _ptt_up(self) -> None:
        if self._gate is not None:
            self._gate.ptt_up()

    def _on_utterance(self, samples: list[float], sample_rate: int) -> None:
        self.after(0, lambda: self._transcribe_and_run(samples, sample_rate))

    def _transcribe_and_run(self, samples: list[float], sample_rate: int) -> None:
        if self._busy:
            return
        self._busy = True
        self._show_listening("vad")
        self._set_status("transcribing…")

        def work() -> None:
            try:
                if isinstance(self._stt, ParakeetSTTProvider):
                    text = self._stt.transcribe_samples(samples, sample_rate)
                else:
                    text = self._stt.transcribe(None)
                if not text.strip():
                    self.after(0, lambda: self._fail("I did not catch that."))
                    return
                self.after(0, lambda: self._run_turn(text))
            except PlatformUnsupported as exc:
                self.after(0, lambda: self._fail(exc.message))
            except Exception as exc:
                self.after(0, lambda: self._fail(str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def _hide(self) -> None:
        if self._awaiting_confirm:
            return
        self.withdraw()
        self.transcript.configure(text="")
        self._set_status("listening for you")

    def _schedule_hide(self) -> None:
        self._cancel_hide()
        self._hide_job = self.after(HIDE_AFTER_MS, self._hide)

    def _cancel_hide(self) -> None:
        if self._hide_job is not None:
            self.after_cancel(self._hide_job)
            self._hide_job = None

    def _quit(self) -> None:
        if self._gate is not None:
            self._gate.stop()
        if self._hotkey is not None:
            self._hotkey.stop()
        self.destroy()

    def _start_drag(self, event) -> None:
        self._drag = (event.x_root, event.y_root)

    def _on_drag(self, event) -> None:
        dx = event.x_root - self._drag[0]
        dy = event.y_root - self._drag[1]
        self._drag = (event.x_root, event.y_root)
        self.geometry(f"+{self.winfo_x() + dx}+{self.winfo_y() + dy}")

    def _draw_orb(self, phase: float) -> None:
        self.canvas.delete("all")
        cx, cy = 44, 44
        breathe = 4 * math.sin(phase)
        r = 30 + breathe
        self.canvas.create_oval(
            cx - r - 8, cy - r - 6, cx + r + 10, cy + r + 12, fill=MIST, outline=""
        )
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=PULSE, outline="")
        self.canvas.create_oval(
            cx - r + 8, cy - r + 6, cx + r - 14, cy + r - 16, fill=MOSS_SOFT, outline=""
        )
        self.canvas.create_oval(cx - 6, cy - 18, cx + 8, cy + 10, fill=MOSS, outline="")
        self.canvas.create_oval(cx + 4, cy - 6, cx + 16, cy + 8, fill=MOSS, outline="")
        self.canvas.create_oval(cx - 14, cy - 2, cx - 2, cy + 10, fill=MOSS, outline="")
        self.canvas.create_oval(cx - 5, cy - 4, cx + 5, cy + 4, fill=CREAM, outline="")

    def _animate(self) -> None:
        if str(self.winfo_viewable()) == "1":
            self._phase += 0.12 if not self._busy else 0.28
            self._draw_orb(self._phase)
        self.after(40, self._animate)

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def _speak_later(self, text: str) -> None:
        self.after(0, lambda: self._set_status(text))

    def _on_engine_event(self, event: AssistantEvent) -> None:
        def apply() -> None:
            if event.text:
                self.transcript.configure(text=event.text)
            if event.state == AssistantState.CONFIRM:
                self._awaiting_confirm = True
                self._cancel_hide()
                self.deiconify()
                self.confirm_row.pack(fill="x", pady=(4, 0))
                self._set_status("needs a yes")
            elif event.kind != "confirm":
                self.confirm_row.pack_forget()
            if event.state == AssistantState.THINKING:
                self._set_status("thinking…")
            elif event.state == AssistantState.DONE:
                self._set_status("done")
                if not self._awaiting_confirm:
                    self._schedule_hide()
            elif event.state == AssistantState.IDLE and event.kind in {
                "speak",
                "refuse",
                "error",
            }:
                self._set_status(event.text or "ok")
                if not self._awaiting_confirm:
                    self._schedule_hide()

        self.after(0, apply)

    def _wait_for_confirm(self, _call: ToolCall) -> bool:
        self._confirm_event.clear()
        self._confirm_yes = False
        self._confirm_event.wait(timeout=60)
        return self._confirm_yes

    def _resolve_confirm(self, yes: bool) -> None:
        self._confirm_yes = yes
        self._awaiting_confirm = False
        self.confirm_row.pack_forget()
        self._confirm_event.set()

    def _fail(self, message: str) -> None:
        self._busy = False
        self.deiconify()
        self._set_status(message)
        self.transcript.configure(text=message)
        self._schedule_hide()

    def _run_turn(self, text: str) -> None:
        self._busy = True
        self.deiconify()
        self.transcript.configure(text=text)
        self._set_status("thinking…")

        def work() -> None:
            try:
                self._engine.handle_transcript(text)
            finally:
                self.after(0, lambda: setattr(self, "_busy", False))

        threading.Thread(target=work, daemon=True).start()


def run_ui() -> None:
    app = FuzzyOrb()
    app.mainloop()


def main() -> None:
    run_ui()


if __name__ == "__main__":
    main()

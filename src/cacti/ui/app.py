from __future__ import annotations

import math
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
from cacti.settings import CactiSettings, load_settings, save_settings
from cacti.ui.client import ControlClient
from cacti.ui.theme import CREAM, INK, MIST, MOSS, MOSS_SOFT, PULSE, SAND
from cacti.ui.tray import start_tray

HIDE_AFTER_MS = 2800


class FuzzyOrb(tk.Toplevel):
    """Appears only after VAD, PTT, or a typed command from the client."""

    def __init__(self, master: tk.Misc, shell: "CactiShell") -> None:
        super().__init__(master)
        self.shell = shell
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.97)
        except tk.TclError:
            pass
        self.configure(bg=SAND)
        self.withdraw()
        self._phase = 0.0
        self._drag = (0, 0)
        self._hide_job: str | None = None
        self._build()
        self.after(40, self._animate)
        self.after(80, self._place_corner)
        self.bind("<Escape>", lambda _e: self.hide())

    def _build(self) -> None:
        card = tk.Frame(self, bg=SAND)
        card.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(card, width=88, height=88, bg=SAND, highlightthickness=0)
        self.canvas.pack(side="left", padx=(4, 8), pady=4)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonPress-1>", self._start_drag)

        body = tk.Frame(card, bg=SAND)
        body.pack(side="left", fill="both", expand=True, pady=6)

        top = tk.Frame(body, bg=SAND)
        top.pack(fill="x")
        title_font = tkfont.Font(family="Georgia", size=16, slant="italic")
        tk.Label(top, text="cacti", fg=MOSS, bg=SAND, font=title_font, anchor="w").pack(
            side="left"
        )
        tk.Button(
            top,
            text="settings",
            command=self.shell.show_client,
            bg=MIST,
            fg=MOSS,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 8),
            padx=8,
        ).pack(side="right")

        self.status = tk.Label(
            body, text="", fg=MOSS_SOFT, bg=SAND, font=("Segoe UI", 10), anchor="w"
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
            text="Yes, do it",
            command=lambda: self.shell.resolve_confirm(True),
            bg=MOSS,
            fg=CREAM,
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
        ).pack(side="left")
        tk.Button(
            self.confirm_row,
            text="Cancel",
            command=lambda: self.shell.resolve_confirm(False),
            bg=MIST,
            fg=INK,
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=(8, 0))

        self.entry = tk.Entry(body, bg=CREAM, fg=INK, relief="flat", font=("Segoe UI", 11))
        self.entry.bind("<Return>", self._typed)
        self.hint = tk.Label(
            body, text="", fg=MOSS_SOFT, bg=SAND, font=("Segoe UI", 8), anchor="w"
        )
        self.hint.pack(fill="x", pady=(8, 0))
        self._draw_orb(0.0)
        self.refresh_copy()

    def refresh_copy(self) -> None:
        cfg = self.shell.settings
        parts = []
        if cfg.ptt_enabled:
            parts.append(f"hold {cfg.ptt_label()} to talk")
        if cfg.vad_enabled:
            parts.append("speak to wake")
        parts.append("Esc hides")
        self.hint.configure(text=" · ".join(parts))
        if cfg.typed_commands:
            if not self.entry.winfo_ismapped():
                self.entry.pack(fill="x", pady=(8, 0), ipady=6, before=self.hint)
        else:
            self.entry.pack_forget()

    def _place_corner(self) -> None:
        self.update_idletasks()
        w, h = 440, 188
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{sw - w - 28}+{sh - h - 72}")

    def show_listening(self, kind: str) -> None:
        self._cancel_hide()
        self.deiconify()
        self.lift()
        key = self.shell.settings.ptt_label()
        label = f"holding {key}…" if kind == "ptt" else "heard you…"
        self.status.configure(text=label)
        self.transcript.configure(text="")

    def hide(self) -> None:
        if self.shell.awaiting_confirm:
            return
        self.withdraw()
        self.transcript.configure(text="")

    def schedule_hide(self) -> None:
        if not self.shell.settings.hide_after_turn:
            return
        self._cancel_hide()
        self._hide_job = self.after(HIDE_AFTER_MS, self.hide)

    def _cancel_hide(self) -> None:
        if self._hide_job is not None:
            self.after_cancel(self._hide_job)
            self._hide_job = None

    def _typed(self, _event=None) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.shell.run_turn(text)

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
        r = 30 + 4 * math.sin(phase)
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
            self._phase += 0.28 if self.shell.busy else 0.12
            self._draw_orb(self._phase)
        self.after(40, self._animate)


class CactiShell(tk.Tk):
    """Root process: settings client + hidden orb + optional tray."""

    def __init__(self) -> None:
        super().__init__()
        self.withdraw()
        self.title("cacti")
        self.settings = load_settings()
        self.busy = False
        self.awaiting_confirm = False
        self._confirm_event = threading.Event()
        self._confirm_yes = False
        self._gate: MicGate | None = None
        self._hotkey: PushToTalkHotkey | None = None
        self._tray = None
        self._stt = get_stt_provider(settings=self.settings)
        self._engine = AssistantEngine(
            speak=lambda text: self.after(0, lambda: self.orb.status.configure(text=text)),
            on_event=self._on_engine_event,
            confirm=self._wait_for_confirm,
            tool_allowed=lambda name: self.settings.tool_enabled(name),
        )
        self.orb = FuzzyOrb(self, self)
        self.client = ControlClient(self, settings=self.settings, on_apply=self.apply_from_client)
        if self.settings.first_run_complete and self._tray is not None:
            self.client.withdraw()
        else:
            self.client.deiconify()
            self.client.lift()
        self._tray = start_tray(
            on_open=lambda: self.after(0, self.show_client),
            on_quit=lambda: self.after(0, self.quit_app),
        )
        self.after(160, self.restart_wake)
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

    def show_client(self) -> None:
        self.client.deiconify()
        self.client.lift()
        try:
            self.client.focus_force()
        except tk.TclError:
            pass

    def apply_from_client(self, settings: CactiSettings, command: str | None = None) -> None:
        settings.first_run_complete = True
        self.settings = settings
        save_settings(settings)
        self._stt = get_stt_provider(settings=settings)
        self.orb.refresh_copy()
        self.restart_wake()
        if command:
            self.run_turn(command)

    def restart_wake(self) -> None:
        if self._gate is not None:
            self._gate.stop()
            self._gate = None
        if self._hotkey is not None:
            self._hotkey.stop()
            self._hotkey = None
        if not self.settings.assistant_enabled:
            return
        need_mic = self.settings.vad_enabled or self.settings.ptt_enabled
        if need_mic:
            try:
                self._gate = MicGate(
                    on_utterance=lambda samples, rate: self.after(
                        0, lambda: self._transcribe(samples, rate)
                    ),
                    on_state=lambda kind: self.after(0, lambda k=kind: self.orb.show_listening(k)),
                    vad=self.settings.vad_enabled,
                    vad_threshold=self.settings.vad_threshold,
                )
                self._gate.start()
            except PlatformUnsupported as exc:
                self.show_client()
                self.orb.status.configure(text=exc.message)
        if self.settings.ptt_enabled:
            try:
                self._hotkey = PushToTalkHotkey(
                    on_down=lambda: self.after(0, self._ptt_down),
                    on_up=lambda: self.after(0, self._ptt_up),
                    key_name=self.settings.ptt_key,
                )
                self._hotkey.start()
            except PlatformUnsupported:
                pass

    def _ptt_down(self) -> None:
        if not self.settings.assistant_enabled or self._gate is None:
            return
        self.orb.show_listening("ptt")
        self._gate.ptt_down()

    def _ptt_up(self) -> None:
        if self._gate is not None:
            self._gate.ptt_up()

    def _transcribe(self, samples: list[float], sample_rate: int) -> None:
        if self.busy or not self.settings.assistant_enabled:
            return
        self.busy = True
        self.orb.show_listening("vad")
        self.orb.status.configure(text="transcribing…")

        def work() -> None:
            try:
                if isinstance(self._stt, ParakeetSTTProvider):
                    text = self._stt.transcribe_samples(samples, sample_rate)
                else:
                    text = self._stt.transcribe(None)
                if not text.strip():
                    self.after(0, lambda: self._fail("I did not catch that."))
                    return
                self.after(0, lambda: self.run_turn(text))
            except PlatformUnsupported as exc:
                self.after(0, lambda: self._fail(exc.message))
            except Exception as exc:
                self.after(0, lambda: self._fail(str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def run_turn(self, text: str) -> None:
        if not self.settings.assistant_enabled:
            self._fail("The assistant is off. Open Cacti and turn it on.")
            return
        self.busy = True
        self.orb.deiconify()
        self.orb.lift()
        self.orb.transcript.configure(text=text)
        self.orb.status.configure(text="thinking…")

        def work() -> None:
            try:
                self._engine.handle_transcript(text)
            finally:
                self.after(0, lambda: setattr(self, "busy", False))

        threading.Thread(target=work, daemon=True).start()

    def _fail(self, message: str) -> None:
        self.busy = False
        self.orb.deiconify()
        self.orb.status.configure(text=message)
        self.orb.transcript.configure(text=message)
        self.orb.schedule_hide()

    def _on_engine_event(self, event: AssistantEvent) -> None:
        def apply() -> None:
            if event.text:
                self.orb.transcript.configure(text=event.text)
            if event.state == AssistantState.CONFIRM:
                self.awaiting_confirm = True
                self.orb._cancel_hide()
                self.orb.deiconify()
                self.orb.confirm_row.pack(fill="x", pady=(4, 0))
                self.orb.status.configure(text="needs a yes")
            elif event.kind != "confirm":
                self.orb.confirm_row.pack_forget()
            if event.state == AssistantState.THINKING:
                self.orb.status.configure(text="thinking…")
            elif event.state in {AssistantState.DONE, AssistantState.IDLE}:
                if event.kind in {"speak", "refuse", "error", "done", "result"}:
                    self.orb.status.configure(text=event.text or "ok")
                    if not self.awaiting_confirm:
                        self.orb.schedule_hide()

        self.after(0, apply)

    def _wait_for_confirm(self, _call: ToolCall) -> bool:
        self._confirm_event.clear()
        self._confirm_yes = False
        self._confirm_event.wait(timeout=60)
        return self._confirm_yes

    def resolve_confirm(self, yes: bool) -> None:
        self._confirm_yes = yes
        self.awaiting_confirm = False
        self.orb.confirm_row.pack_forget()
        self._confirm_event.set()

    def quit_app(self) -> None:
        if self._gate is not None:
            self._gate.stop()
        if self._hotkey is not None:
            self._hotkey.stop()
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.destroy()


def run_ui() -> None:
    CactiShell().mainloop()


def main() -> None:
    run_ui()


if __name__ == "__main__":
    main()

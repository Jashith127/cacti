from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from cacti.assistant.stt.onnx_runtime import describe_asr_device
from cacti.settings import GROUP_LABELS, PTT_KEYS, TOOL_GROUPS, TOOL_LABELS, CactiSettings
from cacti.ui.theme import CREAM, INK, LINE, MIST, MOSS, MOSS_SOFT, SAND, WHITE


class ControlClient(tk.Toplevel):
    """Home for toggles: wake, speech, and which tools cacti is allowed to use."""

    def __init__(self, master: tk.Misc, *, settings: CactiSettings, on_apply) -> None:
        super().__init__(master)
        self.title("Cacti")
        self.configure(bg=SAND)
        self.settings = settings
        self._on_apply = on_apply
        self.resizable(False, False)
        self._vars: dict[str, tk.Variable] = {}
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        self.withdraw()

    def _bool(self, key: str, value: bool) -> tk.BooleanVar:
        var = tk.BooleanVar(value=value)
        self._vars[key] = var
        return var

    def _str(self, key: str, value: str) -> tk.StringVar:
        var = tk.StringVar(value=value)
        self._vars[key] = var
        return var

    def _section(self, parent, title: str) -> tk.Frame:
        wrap = tk.Frame(parent, bg=WHITE, highlightbackground=LINE, highlightthickness=1)
        wrap.pack(fill="x", pady=(0, 12), ipady=8, ipadx=10)
        tk.Label(
            wrap, text=title, bg=WHITE, fg=MOSS, font=("Georgia", 13, "italic"), anchor="w"
        ).pack(fill="x", padx=12, pady=(8, 4))
        body = tk.Frame(wrap, bg=WHITE)
        body.pack(fill="x", padx=12, pady=(0, 8))
        return body

    def _check(self, parent, text: str, var: tk.BooleanVar, hint: str = "") -> None:
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", pady=3)
        tk.Checkbutton(
            row,
            text=text,
            variable=var,
            bg=WHITE,
            fg=INK,
            activebackground=WHITE,
            selectcolor=CREAM,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(side="left")
        if hint:
            tk.Label(row, text=hint, bg=WHITE, fg=MOSS_SOFT, font=("Segoe UI", 8)).pack(
                side="left", padx=(8, 0)
            )

    def _build(self) -> None:
        outer = tk.Frame(self, bg=SAND)
        outer.pack(fill="both", expand=True, padx=18, pady=16)

        header = tk.Frame(outer, bg=SAND)
        header.pack(fill="x", pady=(0, 8))
        tk.Label(
            header, text="cacti", bg=SAND, fg=MOSS, font=("Georgia", 28, "italic"), anchor="w"
        ).pack(fill="x")
        tk.Label(
            header,
            text="A quiet helper. It stays out of the way until you talk or hold the hotkey.",
            bg=SAND,
            fg=MOSS_SOFT,
            font=("Segoe UI", 10),
            wraplength=520,
            justify="left",
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        self.assistant_var = self._bool("assistant_enabled", self.settings.assistant_enabled)
        master = tk.Frame(outer, bg=MOSS)
        master.pack(fill="x", pady=(10, 14), ipady=8, ipadx=8)
        tk.Checkbutton(
            master,
            text="  Assistant is on",
            variable=self.assistant_var,
            bg=MOSS,
            fg=CREAM,
            selectcolor=MOSS_SOFT,
            activebackground=MOSS,
            activeforeground=CREAM,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x", padx=8)

        cmd = tk.Frame(outer, bg=SAND)
        cmd.pack(fill="x", pady=(0, 12))
        tk.Label(cmd, text="Try a command", bg=SAND, fg=INK, font=("Segoe UI", 9)).pack(
            anchor="w"
        )
        self.command = tk.Entry(cmd, bg=CREAM, fg=INK, relief="flat", font=("Segoe UI", 11))
        self.command.pack(fill="x", ipady=7, pady=(4, 0))
        self.command.insert(0, "e.g. mute, open notepad, what’s this window")
        self.command.bind("<FocusIn>", self._clear_cmd)
        self.command.bind("<Return>", self._submit_cmd)

        wake = self._section(outer, "How it wakes")
        self.vad_var = self._bool("vad_enabled", self.settings.vad_enabled)
        self.ptt_var = self._bool("ptt_enabled", self.settings.ptt_enabled)
        self._check(
            wake,
            "Speak to wake",
            self.vad_var,
            "Starts listening when you start talking",
        )
        self._check(
            wake,
            "Push-to-talk",
            self.ptt_var,
            "Hold a key, talk, then release",
        )
        key_row = tk.Frame(wake, bg=WHITE)
        key_row.pack(fill="x", pady=(6, 0))
        tk.Label(key_row, text="Hotkey", bg=WHITE, fg=INK, font=("Segoe UI", 10)).pack(
            side="left"
        )
        self.ptt_key_var = self._str("ptt_key", self.settings.ptt_key)
        keys = ttk.Combobox(
            key_row,
            textvariable=self.ptt_key_var,
            values=list(PTT_KEYS),
            state="readonly",
            width=10,
        )
        keys.pack(side="left", padx=(8, 0))
        tk.Label(
            wake,
            text="F8 is a good default — it rarely fights other apps.",
            bg=WHITE,
            fg=MOSS_SOFT,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        speech = self._section(outer, "Speech")
        self.stt_var = self._str("stt_backend", self.settings.stt_backend)
        tk.Radiobutton(
            speech,
            text="Parakeet v2 (local speech-to-text)",
            variable=self.stt_var,
            value="parakeet",
            bg=WHITE,
            fg=INK,
            selectcolor=CREAM,
            activebackground=WHITE,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x")
        tk.Radiobutton(
            speech,
            text="Typed commands only (no microphone model)",
            variable=self.stt_var,
            value="stub",
            bg=WHITE,
            fg=INK,
            selectcolor=CREAM,
            activebackground=WHITE,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x")
        self.device_var = self._str("asr_device", self.settings.asr_device)
        tk.Radiobutton(
            speech,
            text="Use the GPU if one is available (CUDA / DirectML)",
            variable=self.device_var,
            value="auto",
            bg=WHITE,
            fg=INK,
            selectcolor=CREAM,
            activebackground=WHITE,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", pady=(6, 0))
        tk.Radiobutton(
            speech,
            text="Force CPU",
            variable=self.device_var,
            value="cpu",
            bg=WHITE,
            fg=INK,
            selectcolor=CREAM,
            activebackground=WHITE,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            speech,
            text=f"This PC: {describe_asr_device()}",
            bg=WHITE,
            fg=MOSS_SOFT,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        ui = self._section(outer, "On screen")
        self.hide_var = self._bool("hide_after_turn", self.settings.hide_after_turn)
        self.typed_var = self._bool("typed_commands", self.settings.typed_commands)
        self._check(
            ui,
            "Hide the orb after each command",
            self.hide_var,
            "It comes back on the next wake",
        )
        self._check(ui, "Show a type-to-talk box on the orb", self.typed_var)

        tools = self._section(outer, "What cacti may do")
        tk.Label(
            tools,
            text="Turn off anything you don’t want voice to touch.",
            bg=WHITE,
            fg=MOSS_SOFT,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))
        self.tool_vars: dict[str, tk.BooleanVar] = {}
        for group, names in TOOL_GROUPS.items():
            tk.Label(
                tools,
                text=GROUP_LABELS[group],
                bg=WHITE,
                fg=MOSS,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            ).pack(fill="x", pady=(8, 2))
            for name in names:
                var = tk.BooleanVar(value=self.settings.tool_enabled(name))
                self.tool_vars[name] = var
                self._check(tools, TOOL_LABELS.get(name, name), var)

        actions = tk.Frame(outer, bg=SAND)
        actions.pack(fill="x", pady=(4, 0))
        tk.Button(
            actions,
            text="Save & use these settings",
            command=self._save,
            bg=MOSS,
            fg=CREAM,
            relief="flat",
            padx=16,
            pady=8,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")
        tk.Label(
            actions,
            text="Changes apply immediately. The orb stays hidden until you wake it.",
            bg=SAND,
            fg=MOSS_SOFT,
            font=("Segoe UI", 8),
            wraplength=280,
            justify="left",
        ).pack(side="left", padx=(12, 0))

        self.geometry("560x760")

    def _clear_cmd(self, _event) -> None:
        if self.command.get().startswith("e.g."):
            self.command.delete(0, "end")

    def _submit_cmd(self, _event=None) -> None:
        text = self.command.get().strip()
        if not text or text.startswith("e.g."):
            return
        self.command.delete(0, "end")
        self._on_apply(self.collect(), command=text)

    def collect(self) -> CactiSettings:
        tools = {name: var.get() for name, var in self.tool_vars.items()}
        return CactiSettings(
            assistant_enabled=bool(self.assistant_var.get()),
            vad_enabled=bool(self.vad_var.get()),
            ptt_enabled=bool(self.ptt_var.get()),
            ptt_key=str(self.ptt_key_var.get()),
            stt_backend=str(self.stt_var.get()),
            asr_device=str(self.device_var.get()),
            hide_after_turn=bool(self.hide_var.get()),
            typed_commands=bool(self.typed_var.get()),
            first_run_complete=True,
            vad_threshold=self.settings.vad_threshold,
            enabled_tools=tools,
        )

    def _save(self) -> None:
        self._on_apply(self.collect(), command=None)

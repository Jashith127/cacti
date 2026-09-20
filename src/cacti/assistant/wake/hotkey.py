from __future__ import annotations

import os
import threading
from collections.abc import Callable

from cacti.errors import PlatformUnsupported

DEFAULT_PTT_KEY = "f8"


class PushToTalkHotkey:
    """Global hold-to-talk. Press starts capture, release ends the utterance."""

    def __init__(
        self,
        *,
        on_down: Callable[[], None],
        on_up: Callable[[], None],
        key_name: str | None = None,
    ) -> None:
        self._on_down = on_down
        self._on_up = on_up
        self.key_name = (key_name or os.environ.get("CACTI_PTT_KEY", DEFAULT_PTT_KEY)).lower()
        self._listener = None
        self._held = False
        self._lock = threading.Lock()

    def start(self) -> None:
        try:
            from pynput import keyboard
        except ImportError as exc:
            raise PlatformUnsupported(
                "Global push-to-talk needs pynput (pip install -e '.[asr]')."
            ) from exc

        target = self._resolve_key(keyboard)

        def on_press(key) -> None:
            if key != target:
                return
            with self._lock:
                if self._held:
                    return
                self._held = True
            self._on_down()

        def on_release(key) -> None:
            if key != target:
                return
            with self._lock:
                if not self._held:
                    return
                self._held = False
            self._on_up()

        self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _resolve_key(self, keyboard_mod):
        name = self.key_name.replace(" ", "")
        special = {
            "f8": keyboard_mod.Key.f8,
            "f9": keyboard_mod.Key.f9,
            "f10": keyboard_mod.Key.f10,
            "rctrl": keyboard_mod.Key.ctrl_r,
            "ctrl_r": keyboard_mod.Key.ctrl_r,
            "ralt": keyboard_mod.Key.alt_r,
            "alt_r": keyboard_mod.Key.alt_r,
            "space": keyboard_mod.Key.space,
        }
        if name in special:
            return special[name]
        if len(name) == 1:
            return keyboard_mod.KeyCode.from_char(name)
        return keyboard_mod.Key.f8

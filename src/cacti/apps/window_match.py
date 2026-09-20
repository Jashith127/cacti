from __future__ import annotations

from pathlib import PureWindowsPath

from cacti.apps.models import WindowMatchSpec


def window_match_from_exe(display_name: str, exe_path: str | None) -> WindowMatchSpec:
    titles: list[str] = []
    if display_name:
        titles.append(display_name)
        # Drop trailing " (something)" for title matching
        base = display_name.split(" (")[0].strip()
        if base and base != display_name:
            titles.append(base)

    processes: list[str] = []
    if exe_path and exe_path.lower().endswith(".exe"):
        processes.append(PureWindowsPath(exe_path.replace("/", "\\")).name)

    return WindowMatchSpec(
        title_substrings=tuple(dict.fromkeys(titles)),
        process_names=tuple(dict.fromkeys(processes)),
    )

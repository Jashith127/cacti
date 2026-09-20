from __future__ import annotations

import os
import sys
from pathlib import Path

from cacti.apps.discovery._records import RawAppRecord


def _start_menu_roots() -> list[Path]:
    roots: list[Path] = []
    program_data = os.environ.get("PROGRAMDATA", "")
    if program_data:
        roots.append(
            Path(program_data) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        )
    appdata = os.environ.get("APPDATA", "")
    if appdata:
        roots.append(Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    return [r for r in roots if r.is_dir()]


def _resolve_lnk(lnk_path: Path) -> tuple[str, str, str] | None:
    try:
        import win32com.client  # type: ignore[import-untyped]
    except ImportError:
        return None

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(lnk_path))
        target = str(shortcut.Targetpath or "").strip()
        args = str(shortcut.Arguments or "").strip()
        work = str(shortcut.WorkingDirectory or "").strip()
        if not target:
            return None
        return target, args, work
    except Exception:
        return None


def discover_start_menu_apps() -> list[RawAppRecord]:
    if sys.platform != "win32":
        return []

    records: list[RawAppRecord] = []
    for root in _start_menu_roots():
        for lnk in root.rglob("*.lnk"):
            resolved = _resolve_lnk(lnk)
            if not resolved:
                continue
            target, args, work = resolved
            if not target.lower().endswith(".exe"):
                continue
            if not Path(target).exists():
                continue
            display = lnk.stem
            records.append(
                RawAppRecord(
                    display_name=display,
                    source="start_menu",
                    exe_path=target,
                    arguments=args,
                    working_directory=work,
                    extra_names=(display,),
                )
            )
    return records

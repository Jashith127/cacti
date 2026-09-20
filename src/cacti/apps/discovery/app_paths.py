from __future__ import annotations

import sys
from pathlib import Path

from cacti.apps.discovery._records import RawAppRecord


def discover_app_paths() -> list[RawAppRecord]:
    if sys.platform != "win32":
        return []

    try:
        import winreg
    except ImportError:
        return []

    records: list[RawAppRecord] = []
    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, key_path) as paths_key:
                index = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(paths_key, index)
                    except OSError:
                        break
                    index += 1
                    if not sub_name.lower().endswith(".exe"):
                        continue
                    try:
                        with winreg.OpenKey(paths_key, sub_name) as app_key:
                            exe, _ = winreg.QueryValueEx(app_key, "")
                    except OSError:
                        continue
                    exe = str(exe).strip()
                    if not exe or not Path(exe).exists():
                        continue
                    display = Path(sub_name).stem
                    records.append(
                        RawAppRecord(
                            display_name=display,
                            source="app_paths",
                            exe_path=exe,
                            extra_names=(display, sub_name),
                        )
                    )
        except OSError:
            continue
    return records

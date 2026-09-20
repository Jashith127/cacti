from __future__ import annotations

import sys
from pathlib import Path

from cacti.apps.discovery._records import RawAppRecord

_UNINSTALL_HIVES = (
    (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", True),
    (r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", True),
    (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", False),
)


def _read_install_location(key) -> str:
    import winreg

    for name in ("InstallLocation", "InstallSource"):
        try:
            value, _ = winreg.QueryValueEx(key, name)
            if value:
                return str(value).strip()
        except OSError:
            continue
    return ""


def _read_display_icon(key) -> str | None:
    import winreg

    try:
        icon, _ = winreg.QueryValueEx(key, "DisplayIcon")
    except OSError:
        return None
    icon = str(icon).strip().strip('"')
    if not icon:
        return None
    if "," in icon:
        icon = icon.split(",", 1)[0].strip().strip('"')
    if icon.lower().endswith(".exe") and Path(icon).exists():
        return icon
    return None


def _read_display_name(key) -> str | None:
    import winreg

    for name in ("DisplayName", "QuietDisplayName"):
        try:
            value, _ = winreg.QueryValueEx(key, name)
            if value and not str(value).startswith(("{", "@")):
                return str(value).strip()
        except OSError:
            continue
    return None


def discover_uninstall_registry() -> list[RawAppRecord]:
    if sys.platform != "win32":
        return []

    import winreg

    records: list[RawAppRecord] = []
    seen: set[str] = set()

    for key_path, use_local_machine in _UNINSTALL_HIVES:
        hive = winreg.HKEY_LOCAL_MACHINE if use_local_machine else winreg.HKEY_CURRENT_USER
        try:
            with winreg.OpenKey(hive, key_path) as uninstall_key:
                index = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(uninstall_key, index)
                    except OSError:
                        break
                    index += 1
                    try:
                        with winreg.OpenKey(uninstall_key, sub_name) as app_key:
                            display = _read_display_name(app_key)
                            if not display:
                                continue
                            try:
                                system_component, _ = winreg.QueryValueEx(
                                    app_key, "SystemComponent"
                                )
                                if int(system_component) == 1:
                                    continue
                            except OSError:
                                pass
                            exe = _read_display_icon(app_key)
                            install_loc = _read_install_location(app_key)
                            if not exe and install_loc:
                                guess = Path(install_loc)
                                if guess.is_dir():
                                    for name in ("launcher.exe", f"{guess.name}.exe"):
                                        candidate = guess / name
                                        if candidate.exists():
                                            exe = str(candidate)
                                            break
                            if not exe:
                                continue
                            dedupe = f"{display.lower()}\0{exe.lower()}"
                            if dedupe in seen:
                                continue
                            seen.add(dedupe)
                            records.append(
                                RawAppRecord(
                                    display_name=display,
                                    source="uninstall_registry",
                                    exe_path=exe,
                                    install_location=install_loc,
                                    extra_names=(display,),
                                )
                            )
                    except OSError:
                        continue
        except OSError:
            continue
    return records

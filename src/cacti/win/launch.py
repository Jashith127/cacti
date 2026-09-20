from __future__ import annotations

import sys

from cacti.apps.models import AppDefinition, LaunchKind
from cacti.errors import PlatformUnsupported


def launch_app(definition: AppDefinition) -> str:
    if sys.platform != "win32":
        raise PlatformUnsupported("Launch requires Windows.")

    launch = definition.launch
    if launch.kind == LaunchKind.SHELL_EXECUTE:
        return _shell_execute(launch.target, launch.arguments, launch.working_directory)
    if launch.kind == LaunchKind.AUMID:
        return _shell_execute(f"shell:AppsFolder\\{launch.target}", "", "")
    if launch.kind == LaunchKind.PROTOCOL:
        return _shell_execute(launch.target, "", "")
    if launch.kind == LaunchKind.SETTINGS_URI:
        return _shell_execute(launch.target, "", "")
    raise PlatformUnsupported(f"Unsupported launch kind: {launch.kind}")


def _shell_execute(target: str, arguments: str, directory: str) -> str:
    import ctypes

    shell32 = ctypes.windll.shell32
    result = shell32.ShellExecuteW(
        None,
        "open",
        target,
        arguments or None,
        directory or None,
        1,
    )
    if int(result) <= 32:
        raise OSError(f"ShellExecute failed with code {int(result)} for {target}")
    return f"Launched {target}"

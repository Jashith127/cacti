from __future__ import annotations

import sys

from cacti.errors import PlatformUnsupported


def lock_workstation() -> str:
    if sys.platform != "win32":
        raise PlatformUnsupported("Lock workstation requires Windows.")
    import ctypes

    ctypes.windll.user32.LockWorkStation()
    return "Workstation locked."


def request_system_sleep() -> str:
    if sys.platform != "win32":
        raise PlatformUnsupported("Sleep requires Windows.")
    import subprocess

    subprocess.run(
        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"],
        check=False,
    )
    return "Sleep requested."

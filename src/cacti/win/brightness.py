from __future__ import annotations

import sys

from cacti.errors import InvalidParameter, PlatformUnsupported


def set_display_brightness_percent(brightness_percent: int) -> str:
    """Set primary display brightness (WMI WmiMonitorBrightnessMethods)."""
    if sys.platform != "win32":
        raise PlatformUnsupported("Brightness control requires Windows.")
    if brightness_percent < 0 or brightness_percent > 100:
        raise InvalidParameter("brightness_percent must be between 0 and 100.")
    import subprocess

    script = f"""
$methods = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods -ErrorAction Stop
$methods.WmiSetBrightness(1, {brightness_percent})
"""
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        raise PlatformUnsupported(
            completed.stderr.strip() or "Brightness WMI call failed on this device."
        )
    return f"Brightness set to {brightness_percent} percent."

from __future__ import annotations

import json
import subprocess
import sys

from cacti.apps.discovery._records import RawAppRecord


def discover_start_apps() -> list[RawAppRecord]:
    """UWP / packaged apps via Get-StartApps (requires PowerShell)."""
    if sys.platform != "win32":
        return []

    script = (
        "Get-StartApps | "
        "Select-Object Name, AppID | "
        "ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []

    if completed.returncode != 0 or not completed.stdout.strip():
        return []

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []

    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        return []

    records: list[RawAppRecord] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = str(item.get("Name", "")).strip()
        app_id = str(item.get("AppID", "")).strip()
        if not name or not app_id:
            continue
        records.append(
            RawAppRecord(
                display_name=name,
                source="start_apps",
                aumid=app_id,
                extra_names=(name,),
            )
        )
    return records

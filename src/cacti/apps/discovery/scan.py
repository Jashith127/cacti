from __future__ import annotations

import sys
import time

from cacti.apps.discovery.app_paths import discover_app_paths
from cacti.apps.discovery.materialize import materialize_record
from cacti.apps.discovery.start_apps import discover_start_apps
from cacti.apps.discovery.start_menu import discover_start_menu_apps
from cacti.apps.discovery.uninstall_registry import discover_uninstall_registry
from cacti.apps.merge import merge_discovered_apps
from cacti.apps.models import AppDefinition, AppRegistrySnapshot
from cacti.errors import PlatformUnsupported


def discover_installed_apps() -> AppRegistrySnapshot:
    """Scan Windows installation surfaces and return a merged app registry snapshot."""
    if sys.platform != "win32":
        raise PlatformUnsupported("App discovery requires Windows 11.")

    raw_rows = []
    raw_rows.extend(discover_start_menu_apps())
    raw_rows.extend(discover_app_paths())
    raw_rows.extend(discover_uninstall_registry())
    raw_rows.extend(discover_start_apps())

    apps: list[AppDefinition] = []
    for row in raw_rows:
        app = materialize_record(row)
        if app is not None:
            apps.append(app)

    merged = merge_discovered_apps(apps)
    return AppRegistrySnapshot(
        version=1,
        generated_at_unix=time.time(),
        apps=tuple(merged),
    )

from __future__ import annotations

from cacti.apps.registry import get_app_registry
from cacti.errors import AppNotFound, PlatformUnsupported
from cacti.needle_shim import tool
from cacti.win.launch import launch_app


@tool
def refresh_app_registry() -> str:
    """Rescan Windows for installed applications and rebuild the local app index cache."""
    registry = get_app_registry()
    try:
        snapshot = registry.refresh()
    except PlatformUnsupported as exc:
        return f"skipped: {exc.message}"
    count = len(snapshot.apps)
    return f"App registry refreshed with {count} entries."


@tool
def launch_application(app_name: str) -> str:
    """Launch an installed application by spoken name or stable app id from the auto-built registry."""
    registry = get_app_registry()
    try:
        app = registry.get_by_id(app_name)
    except AppNotFound:
        app = registry.resolve_spoken_name(app_name)
    return launch_app(app)


@tool
def list_matching_applications(query: str) -> str:
    """Search the auto-built app registry for names matching a spoken query (for disambiguation)."""
    registry = get_app_registry()
    matches = registry.search(query, limit=8)
    if not matches:
        return f"No applications match '{query}'."
    lines = [f"{app.display_name} ({app.id})" for app, _score in matches]
    return "Matches: " + "; ".join(lines)

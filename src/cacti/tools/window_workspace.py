from __future__ import annotations

from typing import Literal

from cacti.apps.registry import get_app_registry
from cacti.errors import AppNotFound
from cacti.needle_shim import tool
from cacti.win.launch import launch_app
from cacti.win.windows_uia import focus_window as _focus_impl
from cacti.win.windows_uia import snap_window as _snap_impl


def _resolve_app(app_name: str):
    registry = get_app_registry()
    try:
        return registry.get_by_id(app_name)
    except AppNotFound:
        return registry.resolve_spoken_name(app_name)


@tool
def focus_window(window_title: str, use_foreground: bool = False) -> str:
    """Focus an existing top-level window by partial title match."""
    app = None
    if window_title.strip() and not use_foreground:
        try:
            app = _resolve_app(window_title)
            return _focus_impl(app=app)
        except AppNotFound:
            pass
    return _focus_impl(window_title, use_foreground=use_foreground)


@tool
def launch_application(app_name: str) -> str:
    """Launch an installed application by spoken name or stable app id from the auto-built registry."""
    return launch_app(_resolve_app(app_name))


@tool
def snap_window(
    region: Literal["left", "right", "maximize"],
    window_title: str = "",
    use_foreground: bool = True,
) -> str:
    """Snap the target window to the left half, right half, or maximize it."""
    app = None
    if window_title.strip() and not use_foreground:
        try:
            app = _resolve_app(window_title)
        except AppNotFound:
            app = None
    return _snap_impl(
        region,
        window_title,
        app=app,
        use_foreground=use_foreground and not window_title.strip(),
    )

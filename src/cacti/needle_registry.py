"""Register all Needle 3 tools for grammar compilation and runtime dispatch."""

from __future__ import annotations

from typing import Callable

from cacti.tools.app_registry_tools import (
    list_matching_applications,
    refresh_app_registry,
)
from cacti.tools.context_screen import (
    get_active_browser_url,
    get_foreground_window_title,
    ocr_foreground_window,
)
from cacti.tools.security_vault import (
    credential_exists_for_target,
    open_credential_manager_settings,
    prompt_credential_for_target,
)
from cacti.tools.system_hardware import (
    set_default_audio_output,
    set_master_volume_percent,
    set_system_mute,
)
from cacti.tools.window_workspace import (
    focus_window,
    launch_application,
    snap_window,
)

ALL_TOOLS: list[Callable[..., object]] = [
    set_master_volume_percent,
    set_system_mute,
    set_default_audio_output,
    focus_window,
    launch_application,
    snap_window,
    get_foreground_window_title,
    get_active_browser_url,
    ocr_foreground_window,
    credential_exists_for_target,
    prompt_credential_for_target,
    open_credential_manager_settings,
    refresh_app_registry,
    list_matching_applications,
]

TOOL_BY_NAME: dict[str, Callable[..., object]] = {fn.__name__: fn for fn in ALL_TOOLS}

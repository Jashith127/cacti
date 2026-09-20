from __future__ import annotations

from cacti.needle_shim import tool


@tool
def credential_exists_for_target(target: str) -> str:
    """Check whether Windows Credential Manager has an entry matching the target name."""
    from cacti.win.credential_manager import credential_exists_for_target as _impl

    return _impl(target)


@tool
def prompt_credential_for_target(target: str) -> str:
    """Obtain a gated credential session reference for the target without speaking the password."""
    from cacti.win.credential_manager import prompt_credential_for_target as _impl

    return _impl(target)


@tool
def open_credential_manager_settings() -> str:
    """Open the Windows Credential Manager control panel for manual credential review."""
    from cacti.win.credential_manager import open_credential_manager_settings as _impl

    return _impl()

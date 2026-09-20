from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawAppRecord:
    """Intermediate row from one discovery source before AppDefinition materialization."""

    display_name: str
    source: str
    exe_path: str | None = None
    arguments: str = ""
    working_directory: str = ""
    aumid: str | None = None
    protocol: str | None = None
    settings_uri: str | None = None
    install_location: str = ""
    extra_names: tuple[str, ...] = ()

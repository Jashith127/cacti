from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LaunchKind(str, Enum):
    SHELL_EXECUTE = "shell_execute"
    AUMID = "aumid"
    PROTOCOL = "protocol"
    SETTINGS_URI = "settings_uri"


@dataclass(frozen=True)
class LaunchSpec:
    kind: LaunchKind
    target: str
    arguments: str = ""
    working_directory: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind.value,
            "target": self.target,
            "arguments": self.arguments,
            "working_directory": self.working_directory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LaunchSpec:
        return cls(
            kind=LaunchKind(data["kind"]),
            target=str(data["target"]),
            arguments=str(data.get("arguments", "")),
            working_directory=str(data.get("working_directory", "")),
        )


@dataclass(frozen=True)
class WindowMatchSpec:
    title_substrings: tuple[str, ...] = ()
    process_names: tuple[str, ...] = ()
    exclude_class_names: tuple[str, ...] = ("Shell_TrayWnd", "Progman")

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "title_substrings": list(self.title_substrings),
            "process_names": list(self.process_names),
            "exclude_class_names": list(self.exclude_class_names),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WindowMatchSpec:
        return cls(
            title_substrings=tuple(data.get("title_substrings", [])),
            process_names=tuple(data.get("process_names", [])),
            exclude_class_names=tuple(
                data.get("exclude_class_names", ["Shell_TrayWnd", "Progman"])
            ),
        )


@dataclass(frozen=True)
class AppDefinition:
    """One launchable desktop target derived from OS discovery (not hand-edited)."""

    id: str
    display_name: str
    spoken_aliases: tuple[str, ...]
    launch: LaunchSpec
    window_match: WindowMatchSpec
    sources: tuple[str, ...] = ()
    install_location: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "spoken_aliases": list(self.spoken_aliases),
            "launch": self.launch.to_dict(),
            "window_match": self.window_match.to_dict(),
            "sources": list(self.sources),
            "install_location": self.install_location,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppDefinition:
        return cls(
            id=str(data["id"]),
            display_name=str(data["display_name"]),
            spoken_aliases=tuple(data.get("spoken_aliases", [])),
            launch=LaunchSpec.from_dict(data["launch"]),
            window_match=WindowMatchSpec.from_dict(data.get("window_match", {})),
            sources=tuple(data.get("sources", [])),
            install_location=str(data.get("install_location", "")),
        )


@dataclass
class AppRegistrySnapshot:
    version: int
    generated_at_unix: float
    apps: tuple[AppDefinition, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at_unix": self.generated_at_unix,
            "apps": [a.to_dict() for a in self.apps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppRegistrySnapshot:
        return cls(
            version=int(data.get("version", 1)),
            generated_at_unix=float(data["generated_at_unix"]),
            apps=tuple(AppDefinition.from_dict(a) for a in data.get("apps", [])),
        )

"""Structured failures for tool execution and TTS mapping."""


class CactiError(Exception):
    """Base error with a short user-facing message."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class PlatformUnsupported(CactiError):
    """Raised when a Win32-only operation runs off Windows."""


class WindowNotFound(CactiError):
    """No HWND matched the requested window criteria."""


class AppNotFound(CactiError):
    """No registry entry matched the app id or spoken alias."""


class InvalidParameter(CactiError):
    """Argument failed validation."""


class RegistryStale(CactiError):
    """Cached app registry is missing and could not be rebuilt."""

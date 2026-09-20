from __future__ import annotations

from cacti.needle_shim import tool


@tool
def get_foreground_window_title() -> str:
    """Return the title text of the current foreground window."""
    from cacti.win.windows_uia import get_foreground_window_title as _impl

    return _impl()


@tool
def get_active_browser_url() -> str:
    """Read the URL from the address bar of the focused Chromium or Edge browser window."""
    from cacti.win.browser_uia import get_active_browser_url as _impl

    return _impl()


@tool
def ocr_foreground_window() -> str:
    """Run OCR on the visible region of the foreground window and return recognized text."""
    from cacti.win.ocr import ocr_foreground_window as _impl

    return _impl()

from __future__ import annotations

import sys

from cacti.errors import PlatformUnsupported, WindowNotFound


def get_active_browser_url() -> str:
    if sys.platform != "win32":
        raise PlatformUnsupported("Browser URL reading requires Windows.")

    try:
        import comtypes.client
        import win32gui
        import win32process
    except ImportError:
        raise PlatformUnsupported("Browser URL reading requires pywin32 and comtypes.")

    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        raise WindowNotFound("No foreground window.")

    _tid, pid = win32process.GetWindowThreadProcessId(hwnd)
    process = _process_name(pid).lower()
    if not any(b in process for b in ("chrome.exe", "msedge.exe", "firefox.exe", "brave.exe")):
        title = win32gui.GetWindowText(hwnd).strip()
        raise WindowNotFound(f"Foreground window is not a supported browser: {title}")

    ui_automation = comtypes.client.CreateObject(
        "{ff48dba4-60ef-4201-aa87-54103eef594e}", interface=None
    )
    element = ui_automation.ElementFromHandle(hwnd)
    if element is None:
        raise WindowNotFound("UI Automation could not access the browser window.")

    url = _find_address_value(element)
    if url:
        return url

    title = win32gui.GetWindowText(hwnd).strip()
    return f"(no address bar value) title: {title}"


def _process_name(pid: int) -> str:
    try:
        import win32api
        import win32process as wp

        handle = win32api.OpenProcess(0x1000, False, pid)
        try:
            exe = wp.GetModuleFileNameEx(handle, 0)
            return exe.split("\\")[-1] if exe else ""
        finally:
            win32api.CloseHandle(handle)
    except Exception:
        return ""


def _find_address_value(element) -> str | None:
    try:
        from comtypes.gen import UIAutomationClient as UIA
    except Exception:
        UIA = None

    try:
        condition = element.CreateTrueCondition() if hasattr(element, "CreateTrueCondition") else None
        if condition is None:
            return _walk_for_edit_value(element, depth=0)
        tree = element.FindAll(4, condition)  # TreeScope_Descendants
        if tree:
            for i in range(tree.Length):
                child = tree.GetElement(i)
                value = _read_edit_value(child)
                if value and value.startswith(("http://", "https://", "edge://", "chrome://")):
                    return value
    except Exception:
        return _walk_for_edit_value(element, depth=0)
    return _walk_for_edit_value(element, depth=0)


def _walk_for_edit_value(element, depth: int) -> str | None:
    if depth > 14:
        return None
    value = _read_edit_value(element)
    if value and (
        value.startswith(("http://", "https://"))
        or "://" in value
        and len(value) > 8
    ):
        return value
    try:
        walker = element
        child = walker.GetFirstChildElement() if hasattr(walker, "GetFirstChildElement") else None
        while child:
            found = _walk_for_edit_value(child, depth + 1)
            if found:
                return found
            child = child.GetNextSiblingElement() if hasattr(child, "GetNextSiblingElement") else None
    except Exception:
        pass
    return None


def _read_edit_value(element) -> str | None:
    try:
        pattern = element.GetCurrentPattern(10002)  # ValuePattern
        if pattern:
            return str(pattern.CurrentValue or "").strip()
    except Exception:
        pass
    try:
        name = element.CurrentName or ""
        if name.lower() in ("address and search bar", "address bar"):
            val = element.CurrentValue or ""
            if val:
                return str(val).strip()
    except Exception:
        pass
    return None

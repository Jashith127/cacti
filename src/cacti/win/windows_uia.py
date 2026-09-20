from __future__ import annotations

import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from cacti.apps.models import AppDefinition, WindowMatchSpec
from cacti.errors import InvalidParameter, PlatformUnsupported, WindowNotFound


@dataclass(frozen=True)
class WindowTarget:
    hwnd: int
    title: str
    process_name: str


def _require_windows() -> None:
    if sys.platform != "win32":
        raise PlatformUnsupported("Window management requires Windows.")


def _enum_top_level_windows() -> list[WindowTarget]:
    import win32gui
    import win32process

    results: list[WindowTarget] = []

    def callback(hwnd: int, _: list[WindowTarget]) -> bool:
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return True
        _tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            import win32api

            handle = win32api.OpenProcess(0x1000, False, pid)
            try:
                import win32process as wp

                exe = wp.GetModuleFileNameEx(handle, 0)
                process_name = exe.split("\\")[-1] if exe else ""
            finally:
                win32api.CloseHandle(handle)
        except Exception:
            process_name = ""
        results.append(WindowTarget(hwnd=hwnd, title=title, process_name=process_name))
        return True

    win32gui.EnumWindows(callback, results)
    return results


def _score_window(
    window: WindowTarget,
    title_query: str,
    match: WindowMatchSpec | None,
) -> float:
    query = title_query.strip().lower()
    best = 0.0
    if query:
        if query == window.title.lower():
            best = max(best, 1.0)
        elif query in window.title.lower():
            best = max(best, 0.9)
        else:
            best = max(best, SequenceMatcher(None, query, window.title.lower()).ratio())

    if match:
        for proc in match.process_names:
            if proc.lower() == window.process_name.lower():
                best = max(best, 0.92)
        for sub in match.title_substrings:
            sub_l = sub.lower()
            if sub_l in window.title.lower():
                best = max(best, 0.88)

    return best


def resolve_window(
    window_title: str = "",
    *,
    app: AppDefinition | None = None,
    use_foreground: bool = False,
) -> WindowTarget:
    _require_windows()
    import win32gui
    import win32process

    if use_foreground:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            raise WindowNotFound("No foreground window.")
        title = win32gui.GetWindowText(hwnd).strip() or "(untitled)"
        _tid, pid = win32process.GetWindowThreadProcessId(hwnd)
        return WindowTarget(hwnd=hwnd, title=title, process_name=_process_name(pid))

    windows = _enum_top_level_windows()
    match_spec = app.window_match if app else None
    query = window_title or (app.display_name if app else "")
    if not query.strip():
        raise InvalidParameter("Provide window_title, app, or use_foreground.")

    scored = [(w, _score_window(w, query, match_spec)) for w in windows]
    scored.sort(key=lambda t: t[1], reverse=True)
    if not scored or scored[0][1] < 0.55:
        hints = ", ".join(w.title for w, _ in scored[:5])
        raise WindowNotFound(f"No window matched '{query}'. Visible: {hints}")

    return scored[0][0]


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


def _focus_hwnd(hwnd: int) -> None:
    import win32api
    import win32con
    import win32gui
    import win32process

    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    foreground = win32gui.GetForegroundWindow()
    if foreground == hwnd:
        return

    fg_thread, _ = win32process.GetWindowThreadProcessId(foreground)
    target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)
    win32api.AttachThreadInput(target_thread, fg_thread, True)
    try:
        win32gui.SetForegroundWindow(hwnd)
        win32gui.BringWindowToTop(hwnd)
    finally:
        win32api.AttachThreadInput(target_thread, fg_thread, False)


def get_foreground_window_title() -> str:
    _require_windows()
    import win32gui

    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        raise WindowNotFound("No foreground window.")
    title = win32gui.GetWindowText(hwnd).strip()
    if not title:
        return "(untitled window)"
    return title


def focus_window(
    window_title: str = "",
    *,
    app: AppDefinition | None = None,
    use_foreground: bool = False,
) -> str:
    target = resolve_window(window_title, app=app, use_foreground=use_foreground)
    _focus_hwnd(target.hwnd)
    return f"Focused '{target.title}'."


def close_window(
    window_title: str = "",
    *,
    app: AppDefinition | None = None,
    use_foreground: bool = False,
) -> str:
    import win32con
    import win32gui

    target = resolve_window(window_title, app=app, use_foreground=use_foreground)
    win32gui.PostMessage(target.hwnd, win32con.WM_CLOSE, 0, 0)
    return f"Close sent to '{target.title}'."


def snap_window(
    region: str,
    window_title: str = "",
    *,
    app: AppDefinition | None = None,
    use_foreground: bool = False,
) -> str:
    import win32con
    import win32gui

    target = resolve_window(
        window_title,
        app=app,
        use_foreground=use_foreground or not window_title.strip(),
    )
    hwnd = target.hwnd
    _focus_hwnd(hwnd)

    region_l = region.strip().lower()
    if region_l == "maximize":
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        return f"Maximized '{target.title}'."

    monitor = win32gui.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
    info = win32gui.GetMonitorInfo(monitor)
    work = info["Work"]
    left, top, right, bottom = work
    width = right - left
    height = bottom - top

    if region_l == "left":
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            left,
            top,
            width // 2,
            height,
            win32con.SWP_SHOWWINDOW,
        )
        return f"Snapped '{target.title}' to the left half."

    if region_l == "right":
        half = width // 2
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            left + half,
            top,
            half,
            height,
            win32con.SWP_SHOWWINDOW,
        )
        return f"Snapped '{target.title}' to the right half."

    raise InvalidParameter("region must be 'left', 'right', or 'maximize'.")

from __future__ import annotations

import sys

from cacti.errors import PlatformUnsupported, WindowNotFound


def ocr_foreground_window() -> str:
    if sys.platform != "win32":
        raise PlatformUnsupported("OCR requires Windows.")

    try:
        import win32gui
        import win32ui
        from PIL import Image
    except ImportError:
        raise PlatformUnsupported("OCR requires pywin32 and Pillow (pip install pywin32 Pillow).")

    hwnd = win32gui.GetForegroundWindow()
    if not hwnd or win32gui.IsIconic(hwnd):
        raise WindowNotFound("Foreground window is not available for OCR.")

    rect = win32gui.GetWindowRect(hwnd)
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        raise WindowNotFound("Foreground window has no visible area.")

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(bitmap)
    save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), 3)  # SRCCOPY

    bmpinfo = bitmap.GetInfo()
    bmpstr = bitmap.GetBitmapBits(True)
    image = Image.frombuffer(
        "RGB",
        (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
        bmpstr,
        "raw",
        "BGRX",
        0,
        1,
    )

    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    return _ocr_image(image)


def _ocr_image(image) -> str:
    try:
        import asyncio

        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.storage.streams import DataWriter, InMemoryRandomAccessStream
    except ImportError:
        return _ocr_tesseract_fallback(image)

    # WinRT path is async; use tesseract fallback for simpler scaffold when winsdk missing.
    return _ocr_tesseract_fallback(image)


def _ocr_tesseract_fallback(image) -> str:
    try:
        import pytesseract
    except ImportError:
        raise PlatformUnsupported(
            "OCR requires winsdk or pytesseract (pip install pytesseract Pillow)."
        )
    text = pytesseract.image_to_string(image).strip()
    if not text:
        return "(no text recognized)"
    return text

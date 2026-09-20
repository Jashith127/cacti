from __future__ import annotations

from collections.abc import Callable


def start_tray(*, on_open: Callable[[], None], on_quit: Callable[[], None]) -> object | None:
    """Optional system-tray home while the orb is hidden."""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        return None

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 8, 60, 62), fill=(155, 184, 164, 255))
    draw.ellipse((22, 6, 42, 48), fill=(63, 93, 74, 255))
    draw.ellipse((36, 22, 54, 40), fill=(63, 93, 74, 255))
    draw.ellipse((12, 24, 28, 42), fill=(63, 93, 74, 255))

    menu = pystray.Menu(
        pystray.MenuItem("Open Cacti", lambda _icon, _item: on_open(), default=True),
        pystray.MenuItem("Quit", lambda _icon, _item: on_quit()),
    )
    icon = pystray.Icon("cacti", image, "cacti", menu)
    icon.run_detached()
    return icon

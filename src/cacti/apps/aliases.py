from __future__ import annotations

import re
import unicodedata
from pathlib import PureWindowsPath


_NOISE_WORDS = frozenset(
    {
        "the",
        "app",
        "application",
        "for",
        "windows",
        "desktop",
        "client",
        "64",
        "32",
        "x64",
        "x86",
        "edition",
        "version",
    }
)


def _normalize_phrase(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^\w\s.-]", " ", ascii_text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip().lower()


def generate_spoken_aliases(
    display_name: str,
    *,
    exe_path: str | None = None,
    extra_names: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Build deduplicated voice aliases from display name, exe stem, and discovery labels."""
    candidates: list[str] = []

    def add(raw: str) -> None:
        phrase = _normalize_phrase(raw)
        if len(phrase) >= 2:
            candidates.append(phrase)

    add(display_name)
    for name in extra_names:
        add(name)

    if exe_path:
        stem = PureWindowsPath(exe_path.replace("/", "\\")).stem
        add(stem)

    # Sub-phrases: "visual studio code" -> also "visual studio", "code" if long enough
    words = _normalize_phrase(display_name).split()
    filtered = [w for w in words if w not in _NOISE_WORDS and len(w) > 1]
    if len(filtered) >= 2:
        add(" ".join(filtered[:2]))
    if len(filtered) >= 3:
        add(" ".join(filtered[-2:]))

    seen: set[str] = set()
    ordered: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return tuple(ordered)

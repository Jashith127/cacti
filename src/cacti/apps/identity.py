from __future__ import annotations

import hashlib
import re
import unicodedata


def slugify(text: str, max_len: int = 48) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    if not slug:
        slug = "app"
    return slug[:max_len].rstrip("-")


def stable_app_id(display_name: str, launch_target: str) -> str:
    """Stable id from human name + launch target so rediscovery does not reshuffle ids."""
    digest = hashlib.sha256(f"{launch_target}\0{display_name}".encode("utf-8")).hexdigest()[:8]
    base = slugify(display_name, max_len=40)
    return f"{base}-{digest}"

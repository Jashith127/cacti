from __future__ import annotations

import os
import sys
from pathlib import Path


def default_cache_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", "")
        if base:
            return Path(base) / "cacti"
    return Path.home() / ".cache" / "cacti"


def default_registry_cache_path() -> Path:
    return default_cache_dir() / "app_registry.json"

from __future__ import annotations

import json
from pathlib import Path

from cacti.apps.models import AppRegistrySnapshot


def load_snapshot(path: Path) -> AppRegistrySnapshot | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AppRegistrySnapshot.from_dict(data)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def save_snapshot(path: Path, snapshot: AppRegistrySnapshot) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

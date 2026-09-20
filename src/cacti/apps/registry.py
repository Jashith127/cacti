from __future__ import annotations

import time
from dataclasses import dataclass
from difflib import SequenceMatcher

from cacti.apps.discovery.scan import discover_installed_apps
from cacti.apps.models import AppDefinition, AppRegistrySnapshot
from cacti.apps.paths import default_registry_cache_path
from cacti.apps.persist import load_snapshot, save_snapshot
from cacti.errors import AppNotFound, PlatformUnsupported


DEFAULT_TTL_SECONDS = 24 * 60 * 60


@dataclass
class AppRegistry:
    """Automatically maintained index of installed apps (no hand-edited YAML)."""

    cache_path: str | None = None
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    _snapshot: AppRegistrySnapshot | None = None

    def _path(self):
        if self.cache_path:
            from pathlib import Path

            return Path(self.cache_path)
        return default_registry_cache_path()

    def ensure_loaded(self, *, force_refresh: bool = False) -> AppRegistrySnapshot:
        if force_refresh:
            return self.refresh()

        if self._snapshot is not None and not self._is_stale(self._snapshot):
            return self._snapshot

        cached = load_snapshot(self._path())
        if cached is not None and not self._is_stale(cached):
            self._snapshot = cached
            return cached

        return self.refresh()

    def refresh(self) -> AppRegistrySnapshot:
        snapshot = discover_installed_apps()
        save_snapshot(self._path(), snapshot)
        self._snapshot = snapshot
        return snapshot

    def _is_stale(self, snapshot: AppRegistrySnapshot) -> bool:
        age = time.time() - snapshot.generated_at_unix
        return age > self.ttl_seconds

    def list_apps(self) -> tuple[AppDefinition, ...]:
        return self.ensure_loaded().apps

    def get_by_id(self, app_id: str) -> AppDefinition:
        app_id_norm = app_id.strip().lower()
        for app in self.ensure_loaded().apps:
            if app.id.lower() == app_id_norm:
                return app
        raise AppNotFound(f"No app registered with id '{app_id}'.")

    def resolve_spoken_name(self, phrase: str, *, min_score: float = 0.72) -> AppDefinition:
        """Map free-text ('open slack') to the best matching discovered app."""
        query = phrase.strip().lower()
        if not query:
            raise AppNotFound("Empty app name.")

        best: AppDefinition | None = None
        best_score = 0.0
        for app in self.ensure_loaded().apps:
            for alias in app.spoken_aliases:
                if query == alias or query in alias or alias in query:
                    score = 0.95 if query == alias else 0.85
                else:
                    score = SequenceMatcher(None, query, alias).ratio()
                if score > best_score:
                    best_score = score
                    best = app

        if best is None or best_score < min_score:
            raise AppNotFound(f"No installed app matches '{phrase}'.")
        return best

    def search(self, phrase: str, limit: int = 8) -> list[tuple[AppDefinition, float]]:
        query = phrase.strip().lower()
        scored: list[tuple[AppDefinition, float]] = []
        for app in self.ensure_loaded().apps:
            best = 0.0
            for alias in app.spoken_aliases:
                if query == alias:
                    best = max(best, 1.0)
                elif query in alias or alias in query:
                    best = max(best, 0.88)
                else:
                    best = max(best, SequenceMatcher(None, query, alias).ratio())
            if best > 0.45:
                scored.append((app, best))
        scored.sort(key=lambda t: (-t[1], t[0].display_name.lower()))
        return scored[:limit]


_global_registry: AppRegistry | None = None


def get_app_registry() -> AppRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = AppRegistry()
    return _global_registry


def bootstrap_registry_on_startup() -> AppRegistrySnapshot:
    """Called by the assistant loop: load cache or scan if missing/stale."""
    registry = get_app_registry()
    try:
        return registry.ensure_loaded()
    except PlatformUnsupported:
        raise

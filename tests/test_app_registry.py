from __future__ import annotations

import json
import time
from pathlib import Path

from cacti.apps.aliases import generate_spoken_aliases
from cacti.apps.identity import stable_app_id
from cacti.apps.merge import merge_discovered_apps
from cacti.apps.models import AppDefinition, LaunchKind, LaunchSpec
from cacti.apps.registry import AppRegistry
from cacti.apps.window_match import window_match_from_exe


def _sample_app(
    display: str,
    exe: str,
    app_id: str,
    aliases: tuple[str, ...],
) -> AppDefinition:
    return AppDefinition(
        id=app_id,
        display_name=display,
        spoken_aliases=aliases,
        launch=LaunchSpec(kind=LaunchKind.SHELL_EXECUTE, target=exe),
        window_match=window_match_from_exe(display, exe),
        sources=("test",),
    )


def test_stable_app_id_is_deterministic():
    a = stable_app_id("Slack", r"C:\apps\Slack.exe")
    b = stable_app_id("Slack", r"C:\apps\Slack.exe")
    c = stable_app_id("Slack", r"C:\apps\slack2.exe")
    assert a == b
    assert a != c


def test_merge_unions_aliases_for_same_exe():
    exe = r"C:\Windows\System32\notepad.exe"
    one = _sample_app("Notepad", exe, "notepad-1", ("notepad",))
    two = _sample_app("Notepad", exe, "notepad-2", ("windows notepad",))
    merged = merge_discovered_apps([one, two])
    assert len(merged) == 1
    assert "windows notepad" in merged[0].spoken_aliases
    assert "notepad" in merged[0].spoken_aliases


def _write_fresh_cache(tmp_path: Path) -> Path:
    fixture = Path(__file__).parent / "fixtures" / "sample_registry.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    data["generated_at_unix"] = time.time()
    cache = tmp_path / "app_registry.json"
    cache.write_text(json.dumps(data), encoding="utf-8")
    return cache


def test_resolve_spoken_name_from_fixture(tmp_path: Path):
    _write_fresh_cache(tmp_path)
    cache = tmp_path / "app_registry.json"
    registry = AppRegistry(cache_path=str(cache), ttl_seconds=999999)
    app = registry.resolve_spoken_name("open slack")
    assert app.display_name == "Slack"


def test_generate_aliases_includes_exe_stem():
    aliases = generate_spoken_aliases(
        "Visual Studio Code",
        exe_path=r"C:\Program Files\Microsoft VS Code\Code.exe",
    )
    assert "visual studio code" in aliases
    assert "code" in aliases


def test_search_ranking(tmp_path: Path):
    _write_fresh_cache(tmp_path)
    cache = tmp_path / "app_registry.json"
    registry = AppRegistry(cache_path=str(cache), ttl_seconds=999999)
    hits = registry.search("note")
    assert hits
    assert hits[0][0].display_name == "Notepad"

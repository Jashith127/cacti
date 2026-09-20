from __future__ import annotations

from cacti.apps.models import AppDefinition, LaunchKind, LaunchSpec


def _launch_key(app: AppDefinition) -> str:
    launch = app.launch
    if launch.kind == LaunchKind.AUMID:
        return f"aumid:{launch.target.lower()}"
    if launch.kind == LaunchKind.PROTOCOL:
        return f"proto:{launch.target.lower()}"
    if launch.kind == LaunchKind.SETTINGS_URI:
        return f"settings:{launch.target.lower()}"
    args = launch.arguments.strip().lower()
    return f"exe:{launch.target.lower()}|{args}"


def merge_discovered_apps(candidates: list[AppDefinition]) -> list[AppDefinition]:
    """Collapse duplicate launch targets; union aliases and discovery sources."""
    by_key: dict[str, AppDefinition] = {}

    for app in candidates:
        key = _launch_key(app)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = app
            continue

        aliases = tuple(dict.fromkeys((*existing.spoken_aliases, *app.spoken_aliases)))
        sources = tuple(dict.fromkeys((*existing.sources, *app.sources)))
        titles = tuple(
            dict.fromkeys(
                (
                    *existing.window_match.title_substrings,
                    *app.window_match.title_substrings,
                )
            )
        )
        processes = tuple(
            dict.fromkeys(
                (
                    *existing.window_match.process_names,
                    *app.window_match.process_names,
                )
            )
        )
        display = existing.display_name
        if len(app.display_name) < len(display):
            display = app.display_name

        by_key[key] = AppDefinition(
            id=existing.id,
            display_name=display,
            spoken_aliases=aliases,
            launch=existing.launch,
            window_match=existing.window_match.__class__(
                title_substrings=titles,
                process_names=processes,
                exclude_class_names=existing.window_match.exclude_class_names,
            ),
            sources=sources,
            install_location=existing.install_location or app.install_location,
        )

    return sorted(by_key.values(), key=lambda a: a.display_name.lower())

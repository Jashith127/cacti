from __future__ import annotations

from cacti.apps.aliases import generate_spoken_aliases
from cacti.apps.discovery._records import RawAppRecord
from cacti.apps.identity import stable_app_id
from cacti.apps.models import AppDefinition, LaunchKind, LaunchSpec
from cacti.apps.window_match import window_match_from_exe


def materialize_record(record: RawAppRecord) -> AppDefinition | None:
    if record.aumid:
        launch = LaunchSpec(kind=LaunchKind.AUMID, target=record.aumid)
        launch_key = record.aumid
        exe_for_match = record.exe_path
    elif record.protocol:
        launch = LaunchSpec(kind=LaunchKind.PROTOCOL, target=record.protocol)
        launch_key = record.protocol
        exe_for_match = record.exe_path
    elif record.settings_uri:
        launch = LaunchSpec(kind=LaunchKind.SETTINGS_URI, target=record.settings_uri)
        launch_key = record.settings_uri
        exe_for_match = None
    elif record.exe_path:
        launch = LaunchSpec(
            kind=LaunchKind.SHELL_EXECUTE,
            target=record.exe_path,
            arguments=record.arguments,
            working_directory=record.working_directory,
        )
        launch_key = record.exe_path
        exe_for_match = record.exe_path
    else:
        return None

    display = record.display_name.strip()
    if not display:
        return None

    app_id = stable_app_id(display, launch_key)
    aliases = generate_spoken_aliases(
        display,
        exe_path=exe_for_match,
        extra_names=record.extra_names,
    )
    return AppDefinition(
        id=app_id,
        display_name=display,
        spoken_aliases=aliases,
        launch=launch,
        window_match=window_match_from_exe(display, exe_for_match),
        sources=(record.source,),
        install_location=record.install_location,
    )

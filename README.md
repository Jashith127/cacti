# cacti

Voice-first Windows 11 desktop assistant scaffolding: Needle 3 tool calling, confidence-tier routing (planned), and **automatic app discovery** (no hand-maintained app YAML).

## Automatic app registry

Installed applications are **discovered from the OS**, merged, cached locally, and refreshed on a schedule. You do not edit a static list of apps.

### Discovery sources (Windows 11)

| Source | What it captures |
|--------|------------------|
| **Start Menu** (`*.lnk`) | Primary user-facing shortcuts → resolved `.exe`, args, working dir |
| **App Paths** registry | Registered executables (`chrome.exe`, etc.) |
| **Uninstall** registry | Display names, install locations, `DisplayIcon` executables |
| **Get-StartApps** (PowerShell) | UWP / packaged apps (AUMID / `shell:AppsFolder\...`) |

Each row becomes an `AppDefinition` with:

- **`id`** — stable hash from display name + launch target (survives rescans)
- **`display_name`** — best label from discovery
- **`spoken_aliases`** — generated from display name, exe stem, and sub-phrases (for STT / Needle)
- **`launch`** — `shell_execute`, `aumid`, `protocol`, or `settings_uri`
- **`window_match`** — `process_names` + `title_substrings` for focus / close / snap tools

Duplicates (same exe + args or same AUMID) are **merged**; aliases and sources are unioned.

### When the registry updates

1. **Assistant startup** — `cacti.assistant.bootstrap.startup()` loads cache or scans if missing/stale.
2. **TTL** — default **24 hours**; stale cache triggers a background rescan on next `ensure_loaded()`.
3. **Tool** — `refresh_app_registry()` forces an immediate full rescan (Confirm tier in production).

Cache file: `%LOCALAPPDATA%\cacti\app_registry.json` (Linux dev: `~/.cache/cacti/app_registry.json`).

### How tools use apps

| Tool | Behavior |
|------|----------|
| `launch_application(app_name)` | Resolve by **stable id** or **spoken alias** → `ShellExecute` / AppsFolder |
| `list_matching_applications(query)` | Fuzzy search for disambiguation (“did you mean …?”) |
| `focus_window` / `close_window` (planned) | Use `window_match` from the same registry entry when the user names an app |

Needle sees `app_name: str` (open vocabulary). The router resolves against the live cache; optional future: inject top-N app names into a sub-grammar for edge STT.

### Package layout

```
src/cacti/apps/          # models, merge, aliases, registry, discovery/*
src/cacti/tools/         # @needle.tool wrappers
src/cacti/win/           # ShellExecute, volume, UIA (planned)
```

### Development

```bash
pip install -e ".[dev]"
pytest
```

Full discovery runs on **Windows** with optional `pip install -e ".[windows]"` (`pywin32`). On Linux, unit tests use JSON fixtures; scan raises `PlatformUnsupported`.

## Confidence tiers (planned)

Act ≥ 0.85 (low risk), Confirm 0.50–0.84 or sensitive tools, Refuse &lt; 0.50. Changing default audio output, closing windows, and vault access are **Confirm** even at high model confidence.

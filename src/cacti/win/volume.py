from __future__ import annotations

import sys

from cacti.errors import InvalidParameter, PlatformUnsupported


def _require_windows() -> None:
    if sys.platform != "win32":
        raise PlatformUnsupported("Audio control requires Windows.")


def set_master_volume_percent(volume_percent: int) -> str:
    _require_windows()
    if volume_percent < 0 or volume_percent > 100:
        raise InvalidParameter("volume_percent must be between 0 and 100.")
    scalar = volume_percent / 100.0
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except ImportError:
        raise PlatformUnsupported(
            "Volume control requires pycaw and comtypes (pip install pycaw comtypes)."
        )

    device = AudioUtilities.GetSpeakers()
    interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    volume.SetMasterVolumeLevelScalar(scalar, None)
    return f"Volume set to {volume_percent} percent."


def set_system_mute(muted: bool) -> str:
    _require_windows()
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    except ImportError:
        raise PlatformUnsupported(
            "Mute requires pycaw and comtypes (pip install pycaw comtypes)."
        )

    device = AudioUtilities.GetSpeakers()
    interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = interface.QueryInterface(IAudioEndpointVolume)
    volume.SetMute(1 if muted else 0, None)
    return "Muted." if muted else "Unmuted."


def set_default_audio_output(device_name: str) -> str:
    _require_windows()
    query = device_name.strip().lower()
    if not query:
        raise InvalidParameter("device_name must not be empty.")

    try:
        from pycaw.pycaw import AudioUtilities
    except ImportError:
        raise PlatformUnsupported(
            "Audio output switching requires pycaw (pip install pycaw comtypes)."
        )

    devices = AudioUtilities.GetAllDevices()
    matches: list[tuple[str, str]] = []
    for dev in devices:
        name = (dev.FriendlyName or "").strip()
        if not name:
            continue
        if query in name.lower():
            matches.append((name, dev.id))

    if not matches:
        names = sorted({(d.FriendlyName or "") for d in devices if d.FriendlyName})
        preview = "; ".join(names[:8])
        return f"No device matched '{device_name}'. Available: {preview}"

    chosen_name, chosen_id = matches[0]
    _policy_set_default_endpoint(chosen_id)
    return f"Default audio output set to '{chosen_name}'."


def _policy_set_default_endpoint(device_id: str) -> None:
    import comtypes.client

    policy = comtypes.client.CreateObject(
        "{870af99c-171d-4f9e-af0d-e63df40c2bc9}",
        interface=None,
    )
    policy.SetDefaultEndpoint(device_id, 0)
    policy.SetDefaultEndpoint(device_id, 1)

from __future__ import annotations

from cacti.needle_shim import tool


@tool
def set_master_volume_percent(volume_percent: int) -> str:
    """Set the master output volume to an absolute level from 0 to 100 percent."""
    from cacti.win.volume import set_master_volume_percent as _impl

    return _impl(volume_percent)


@tool
def set_system_mute(muted: bool) -> str:
    """Mute or unmute the default audio output device."""
    from cacti.win.volume import set_system_mute as _impl

    return _impl(muted)


@tool
def set_default_audio_output(device_name: str) -> str:
    """Set the default Windows playback device by matching a partial device name."""
    from cacti.win.volume import set_default_audio_output as _impl

    return _impl(device_name)

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from cacti.errors import CredentialDenied, PlatformUnsupported


class _CREDENTIAL_ATTRIBUTE(ctypes.Structure):
    _fields_ = [
        ("Keyword", wintypes.LPWSTR),
        ("Flags", wintypes.DWORD),
        ("ValueSize", wintypes.DWORD),
        ("Value", ctypes.POINTER(ctypes.c_byte)),
    ]


class _CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.POINTER(_CREDENTIAL_ATTRIBUTE)),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _advapi() -> ctypes.WinDLL:
    if sys.platform != "win32":
        raise PlatformUnsupported("Credential Manager requires Windows.")
    return ctypes.WinDLL("advapi32", use_last_error=True)


def credential_exists_for_target(target: str) -> str:
    advapi = _advapi()
    pcred = ctypes.POINTER(_CREDENTIAL)()
    cred_read = advapi.CredReadW
    cred_read.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(_CREDENTIAL))]
    cred_read.restype = wintypes.BOOL

    query = target.strip()
    if not query:
        return "false: empty target"

    if cred_read(query, 1, 0, ctypes.byref(pcred)):
        advapi.CredFree(pcred)
        return f"true: credential exists for {query}"

    # Prefix search via enumerate
    for name in _enumerate_target_names():
        if query.lower() in name.lower():
            return f"true: credential exists matching {name}"
    return f"false: no credential for {query}"


def prompt_credential_for_target(target: str) -> str:
    """
    Return a session handle reference — never the password in clear text for Act tier.
    Format: session:<target>:<username>
    """
    advapi = _advapi()
    pcred = ctypes.POINTER(_CREDENTIAL)()
    cred_read = advapi.CredReadW
    cred_read.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(_CREDENTIAL))]
    cred_read.restype = wintypes.BOOL

    query = target.strip()
    if not query:
        raise CredentialDenied("Empty credential target.")

    matched = query
    if not cred_read(query, 1, 0, ctypes.byref(pcred)):
        matched = _find_best_target(query)
        if not matched or not cred_read(matched, 1, 0, ctypes.byref(pcred)):
            raise CredentialDenied(f"No stored credential for '{query}'.")

    cred = pcred.contents
    username = cred.UserName or ""
    advapi.CredFree(pcred)
    if not username:
        raise CredentialDenied("Credential found but username is empty.")
    return f"session:{matched}:{username}"


def open_credential_manager_settings() -> str:
    if sys.platform != "win32":
        raise PlatformUnsupported("Credential Manager UI requires Windows.")
    import subprocess

    subprocess.run(
        ["control.exe", "/name", "Microsoft.CredentialManager"],
        check=False,
    )
    return "Opened Windows Credential Manager."


def _enumerate_target_names() -> list[str]:
    advapi = _advapi()
    count = wintypes.DWORD()
    pcreds = ctypes.POINTER(ctypes.POINTER(_CREDENTIAL))()
    if not advapi.CredEnumerateW(None, 0, ctypes.byref(count), ctypes.byref(pcreds)):
        return []
    names: list[str] = []
    for i in range(count.value):
        cred = pcreds[i].contents
        if cred.TargetName:
            names.append(cred.TargetName)
    advapi.CredFree(pcreds)
    return names


def _find_best_target(query: str) -> str | None:
    q = query.lower()
    for name in _enumerate_target_names():
        if q in name.lower():
            return name
    return None

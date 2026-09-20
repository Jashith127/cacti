"""Minimal stand-in until the Needle 3 SDK is wired in this environment."""


def tool(fn):
    fn._needle_tool = True  # type: ignore[attr-defined]
    return fn

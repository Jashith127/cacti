from __future__ import annotations

import logging

from cacti.apps.registry import bootstrap_registry_on_startup
from cacti.errors import PlatformUnsupported

logger = logging.getLogger(__name__)


def startup() -> None:
    """Assistant entry: warm the app registry without blocking the voice loop on failure."""
    try:
        snapshot = bootstrap_registry_on_startup()
        logger.info(
            "App registry ready: %s apps (generated_at=%s)",
            len(snapshot.apps),
            snapshot.generated_at_unix,
        )
    except PlatformUnsupported:
        logger.warning("App registry scan skipped (non-Windows host).")

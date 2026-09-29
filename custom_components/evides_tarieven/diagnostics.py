"""Diagnostics support for Evides Tarieven."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import EvidesConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EvidesConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    Everything here comes from a public web page, so nothing needs redacting.
    """
    coordinator = entry.runtime_data
    return {
        "options": dict(entry.options),
        "update_interval": str(coordinator.update_interval),
        "last_update_success": coordinator.last_update_success,
        "last_exception": repr(coordinator.last_exception)
        if coordinator.last_exception
        else None,
        "data": coordinator.data,
    }

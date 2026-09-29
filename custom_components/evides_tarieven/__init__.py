"""The Evides Tarieven integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_SCAN_INTERVAL_HOURS,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    ISSUE_PAGINA_GEWIJZIGD,
)
from .coordinator import EvidesTariefCoordinator, cache_store

PLATFORMS = [Platform.SENSOR]

type EvidesConfigEntry = ConfigEntry[EvidesTariefCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: EvidesConfigEntry) -> bool:
    """Set up Evides Tarieven from a config entry."""
    hours = entry.options.get(CONF_SCAN_INTERVAL_HOURS, DEFAULT_SCAN_INTERVAL_HOURS)
    coordinator = EvidesTariefCoordinator(
        hass, entry, update_interval=timedelta(hours=hours)
    )
    await coordinator.async_load_cache()
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: EvidesConfigEntry) -> None:
    """Reload the entry when options change (e.g. scan interval)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: EvidesConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: EvidesConfigEntry) -> None:
    """Clean up the tariff cache and repair issue when the integration is deleted."""
    ir.async_delete_issue(hass, DOMAIN, ISSUE_PAGINA_GEWIJZIGD)
    await cache_store(hass, entry).async_remove()

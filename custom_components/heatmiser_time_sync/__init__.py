"""Heatmiser WiFi Time Sync integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PIN, CONF_PORT
from homeassistant.core import CoreState, HomeAssistant

from .const import CONF_SYNC_ON_START, DEFAULT_SYNC_ON_START, DOMAIN, PLATFORMS
from .coordinator import HeatmiserSyncManager
from .protocol import HeatmiserClient

type HeatmiserConfigEntry = ConfigEntry[HeatmiserSyncManager]


async def async_setup_entry(hass: HomeAssistant, entry: HeatmiserConfigEntry) -> bool:
    """Set up one Heatmiser thermostat."""
    client = HeatmiserClient(
        entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_PIN]
    )
    manager = HeatmiserSyncManager(hass, entry, client)
    entry.runtime_data = manager
    manager.start()

    if entry.options.get(CONF_SYNC_ON_START, DEFAULT_SYNC_ON_START):
        if hass.state is CoreState.running:
            entry.async_create_background_task(
                hass, manager.async_sync(), f"Initial Heatmiser clock sync {client.host}"
            )
        else:
            entry.async_on_unload(
                hass.bus.async_listen_once(
                    "homeassistant_started", lambda _event: manager._scheduled_sync(None)
                )
            )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HeatmiserConfigEntry) -> bool:
    """Unload a Heatmiser thermostat."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        entry.runtime_data.stop()
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: HeatmiserConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

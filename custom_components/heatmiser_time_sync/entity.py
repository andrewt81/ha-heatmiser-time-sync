"""Base entity for Heatmiser WiFi Time Sync."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import HeatmiserConfigEntry
from .const import DOMAIN


class HeatmiserEntity(Entity):
    """Base Heatmiser time-sync entity."""

    _attr_has_entity_name = True

    def __init__(self, entry: HeatmiserConfigEntry) -> None:
        self.entry = entry
        self.manager = entry.runtime_data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Heatmiser",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self.manager.add_listener(self.async_write_ha_state))

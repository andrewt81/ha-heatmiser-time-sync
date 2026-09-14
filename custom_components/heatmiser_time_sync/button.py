"""Manual synchronisation button."""

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HeatmiserConfigEntry
from .entity import HeatmiserEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HeatmiserConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([HeatmiserSyncButton(entry)])


class HeatmiserSyncButton(HeatmiserEntity, ButtonEntity):
    """Button that synchronises the thermostat immediately."""

    _attr_translation_key = "sync_clock"

    def __init__(self, entry: HeatmiserConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_sync_clock"

    async def async_press(self) -> None:
        await self.manager.async_sync()

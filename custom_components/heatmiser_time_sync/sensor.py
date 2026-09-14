"""Last successful clock synchronisation sensor."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import HeatmiserConfigEntry
from .entity import HeatmiserEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HeatmiserConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([HeatmiserLastSyncSensor(entry)])


class HeatmiserLastSyncSensor(HeatmiserEntity, SensorEntity):
    """Timestamp and details of the last clock sync."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "last_sync"

    def __init__(self, entry: HeatmiserConfigEntry) -> None:
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_last_sync"

    @property
    def native_value(self):
        return self.manager.last_success

    @property
    def available(self) -> bool:
        return self.manager.last_error is None

    @property
    def extra_state_attributes(self):
        result = self.manager.last_result
        attributes = {"last_error": self.manager.last_error}
        if result is not None:
            attributes.update(
                {
                    "clock_before": result.before.isoformat(),
                    "clock_requested": result.requested.isoformat(),
                    "clock_after": result.after.isoformat(),
                    "model": result.model,
                }
            )
        return attributes

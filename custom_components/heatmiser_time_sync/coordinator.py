"""Scheduling and state management for Heatmiser clock synchronisation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL
from .protocol import HeatmiserClient, SyncResult

_LOGGER = logging.getLogger(__name__)


class HeatmiserSyncManager:
    """Manage periodic and on-demand synchronisation for one thermostat."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HeatmiserClient) -> None:
        self.hass = hass
        self.entry = entry
        self.client = client
        self.last_result: SyncResult | None = None
        self.last_success = None
        self.last_error: str | None = None
        self._listeners: set = set()
        self._cancel_interval = None

    async def async_sync(self) -> None:
        """Synchronise now and notify entities."""
        try:
            self.last_result = await self.client.sync_clock(dt_util.now())
            self.last_success = datetime.now(UTC)
            self.last_error = None
            _LOGGER.info("Clock synchronised for %s", self.client.host)
        except Exception as err:  # Keep future schedules alive after an offline device.
            self.last_error = str(err)
            _LOGGER.warning("Clock synchronisation failed for %s: %s", self.client.host, err)
        self._notify()

    def start(self) -> None:
        """Start periodic synchronisation."""
        interval_hours = self.entry.options.get(CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL)
        self._cancel_interval = async_track_time_interval(
            self.hass, self._scheduled_sync, timedelta(hours=interval_hours)
        )

    @callback
    def _scheduled_sync(self, _now) -> None:
        self.entry.async_create_background_task(
            self.hass, self.async_sync(), f"Heatmiser clock sync {self.client.host}"
        )

    @callback
    def add_listener(self, listener):
        """Register an entity state listener."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    @callback
    def _notify(self) -> None:
        for listener in self._listeners:
            listener()

    @callback
    def stop(self) -> None:
        """Stop scheduling."""
        if self._cancel_interval is not None:
            self._cancel_interval()
            self._cancel_interval = None

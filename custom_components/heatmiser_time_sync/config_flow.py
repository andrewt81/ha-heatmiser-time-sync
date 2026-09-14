"""Config flow for Heatmiser WiFi Time Sync."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PIN, CONF_PORT
from homeassistant.helpers import selector

from .const import (
    CONF_SYNC_INTERVAL,
    CONF_SYNC_ON_START,
    DEFAULT_NAME,
    DEFAULT_PIN,
    DEFAULT_PORT,
    DEFAULT_SYNC_INTERVAL,
    DEFAULT_SYNC_ON_START,
    DOMAIN,
)
from .protocol import HeatmiserAuthError, HeatmiserClient, HeatmiserError


def _device_schema(defaults: dict | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(CONF_PIN, default=defaults.get(CONF_PIN, DEFAULT_PIN)): str,
        }
    )


class HeatmiserConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure one legacy Heatmiser Wi-Fi thermostat."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            pin = user_input[CONF_PIN]
            if not pin.isdigit() or not 0 <= int(pin) <= 65535:
                errors[CONF_PIN] = "invalid_pin"
            else:
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST].strip().lower()}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                client = HeatmiserClient(
                    user_input[CONF_HOST].strip(), user_input[CONF_PORT], pin
                )
                try:
                    await client.read_clock()
                except HeatmiserAuthError:
                    errors["base"] = "invalid_auth"
                except HeatmiserError:
                    errors["base"] = "cannot_connect"
                else:
                    data = dict(user_input)
                    data[CONF_HOST] = data[CONF_HOST].strip()
                    return self.async_create_entry(title=data.pop(CONF_NAME), data=data)

        return self.async_show_form(
            step_id="user", data_schema=_device_schema(user_input), errors=errors
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return HeatmiserOptionsFlow()


class HeatmiserOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input=None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SYNC_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SYNC_INTERVAL, DEFAULT_SYNC_INTERVAL
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=168, step=1, mode=selector.NumberSelectorMode.BOX
                        )
                    ),
                    vol.Required(
                        CONF_SYNC_ON_START,
                        default=self.config_entry.options.get(
                            CONF_SYNC_ON_START, DEFAULT_SYNC_ON_START
                        ),
                    ): bool,
                }
            ),
        )

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CozyLifeAuthError, CozyLifeClient, CozyLifeError
from .const import CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE, DOMAIN


class CozyLifeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CozyLife Sensors."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip().lower()
            password = user_input[CONF_PASSWORD]
            country_code = user_input[CONF_COUNTRY_CODE].strip()

            await self.async_set_unique_id(email)
            self._abort_if_unique_id_configured()

            client = CozyLifeClient(
                async_get_clientsession(self.hass),
                email,
                password,
                country_code,
            )

            try:
                await client.async_login()
                data = await client.async_update_devices()
            except CozyLifeAuthError:
                errors["base"] = "invalid_auth"
            except CozyLifeError:
                errors["base"] = "cannot_connect"
            else:
                if not data:
                    errors["base"] = "no_devices"
                else:
                    return self.async_create_entry(
                        title=email,
                        data={
                            CONF_EMAIL: email,
                            CONF_PASSWORD: password,
                            CONF_COUNTRY_CODE: country_code,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_COUNTRY_CODE, default=DEFAULT_COUNTRY_CODE): str,
                }
            ),
            errors=errors,
        )

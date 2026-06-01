from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CozyLifeClient, CozyLifeDeviceState, CozyLifeError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CozyLifeCoordinator(DataUpdateCoordinator[dict[str, CozyLifeDeviceState]]):
    """Coordinator for CozyLife sensor data."""

    def __init__(
        self,
        hass: HomeAssistant,
        email: str,
        password: str,
        country_code: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = CozyLifeClient(
            async_get_clientsession(hass),
            email,
            password,
            country_code,
        )

    async def _async_update_data(self) -> dict[str, CozyLifeDeviceState]:
        try:
            return await self.client.async_update_devices()
        except CozyLifeError as err:
            raise UpdateFailed(str(err)) from err

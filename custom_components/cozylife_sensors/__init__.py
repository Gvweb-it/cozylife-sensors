from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_COUNTRY_CODE, DOMAIN, PLATFORMS
from .coordinator import CozyLifeCoordinator

type CozyLifeConfigEntry = ConfigEntry[CozyLifeCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CozyLifeConfigEntry) -> bool:
    """Set up CozyLife Sensors from a config entry."""
    coordinator = CozyLifeCoordinator(
        hass,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_COUNTRY_CODE],
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(
        entry, [Platform(platform) for platform in PLATFORMS]
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CozyLifeConfigEntry) -> bool:
    """Unload a CozyLife Sensors config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry, [Platform(platform) for platform in PLATFORMS]
    )

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import CozyLifeDeviceState
from .const import DOMAIN
from .coordinator import CozyLifeCoordinator


@dataclass(frozen=True, kw_only=True)
class CozyLifeSensorEntityDescription(SensorEntityDescription):
    """Description for a CozyLife sensor entity."""

    value_fn: Any


SENSOR_DESCRIPTIONS = (
    CozyLifeSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda state: state.temperature,
    ),
    CozyLifeSensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.humidity,
    ),
    CozyLifeSensorEntityDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda state: state.battery,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CozyLife sensor entities."""
    coordinator: CozyLifeCoordinator = entry.runtime_data
    entities: list[CozyLifeSensor] = []

    for device_id, state in coordinator.data.items():
        for description in SENSOR_DESCRIPTIONS:
            if description.value_fn(state) is not None:
                entities.append(CozyLifeSensor(coordinator, device_id, description))

    async_add_entities(entities)


class CozyLifeSensor(CoordinatorEntity[CozyLifeCoordinator], SensorEntity):
    """Representation of a CozyLife sensor."""

    entity_description: CozyLifeSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CozyLifeCoordinator,
        device_id: str,
        description: CozyLifeSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self.entity_description = description
        self._attr_unique_id = f"{device_id}_{description.key}"

    @property
    def _state(self) -> CozyLifeDeviceState | None:
        return self.coordinator.data.get(self._device_id)

    @property
    def native_value(self) -> float | int | None:
        """Return the state of the sensor."""
        if self._state is None:
            return None
        return self.entity_description.value_fn(self._state)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self._state is not None and self._state.online

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        state = self._state
        if state is None:
            return {"identifiers": {(DOMAIN, self._device_id)}}

        device = state.device
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": device.name,
            "manufacturer": "CozyLife",
            "model": device.model_name or device.product_id,
            "sw_version": device.firmware_version,
            "hw_version": device.firmware_chip,
        }

"""Sensor platform for Evides Tarieven."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_BRON_URL,
    ATTR_JAAR,
    ATTR_JAAR_BRON,
    ATTR_LAATST_GECONTROLEERD,
    DOMAIN,
    KEY_BELASTING_LEIDINGWATER,
    KEY_VARIABEL_TARIEF,
    KEY_VASTRECHT,
)
from .coordinator import EvidesTariefCoordinator


@dataclass(frozen=True, kw_only=True)
class EvidesSensorDescription(SensorEntityDescription):
    """Describes an Evides tarief sensor."""


SENSOR_DESCRIPTIONS: tuple[EvidesSensorDescription, ...] = (
    EvidesSensorDescription(
        key=KEY_VASTRECHT,
        translation_key="vastrecht",
        name="Vastrecht",
        native_unit_of_measurement="EUR",
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:cash",
    ),
    EvidesSensorDescription(
        key=KEY_VARIABEL_TARIEF,
        translation_key="variabel_tarief",
        name="Variabel tarief per m3",
        native_unit_of_measurement="EUR/m³",
        icon="mdi:water",
    ),
    EvidesSensorDescription(
        key=KEY_BELASTING_LEIDINGWATER,
        translation_key="belasting_leidingwater",
        name="Belasting op leidingwater per m3",
        native_unit_of_measurement="EUR/m³",
        icon="mdi:water-percent",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Evides Tarieven sensors from a config entry."""
    coordinator: EvidesTariefCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        EvidesTariefSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class EvidesTariefSensor(CoordinatorEntity[EvidesTariefCoordinator], SensorEntity):
    """Representation of a single Evides tarief value."""

    _attr_has_entity_name = True
    entity_description: EvidesSensorDescription

    def __init__(
        self,
        coordinator: EvidesTariefCoordinator,
        entry: ConfigEntry,
        description: EvidesSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Evides Tarieven",
            manufacturer="Evides",
            entry_type="service",
            configuration_url="https://www.evides.nl/service/tarieven",
        )

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("values", {}).get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        return {
            "jaar": data.get(ATTR_JAAR),
            "jaar_bron": data.get(ATTR_JAAR_BRON),
            "bron_url": data.get(ATTR_BRON_URL),
            "laatst_gecontroleerd": data.get(ATTR_LAATST_GECONTROLEERD),
        }

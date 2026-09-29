"""Sensor platform for Evides Tarieven."""
from __future__ import annotations

import calendar
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import CURRENCY_EURO, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from . import EvidesConfigEntry
from .const import (
    ATTR_BRON_URL,
    ATTR_JAAR,
    ATTR_JAAR_BRON,
    ATTR_LAATST_GECONTROLEERD,
    DOMAIN,
    KEY_BELASTING_LEIDINGWATER,
    KEY_LAATST_GECONTROLEERD,
    KEY_TOTAAL_PER_M3,
    KEY_VARIABEL_TARIEF,
    KEY_VASTRECHT,
    KEY_VASTRECHT_PER_DAG,
    TARIEVEN_URL,
)
from .coordinator import EvidesTariefCoordinator

UNIT_EUR_PER_M3 = f"{CURRENCY_EURO}/m³"


def _scraped(key: str) -> Callable[[dict[str, Any]], float | None]:
    return lambda data: data["values"].get(key)


def _totaal_per_m3(data: dict[str, Any]) -> float | None:
    values = data["values"]
    if KEY_VARIABEL_TARIEF not in values or KEY_BELASTING_LEIDINGWATER not in values:
        return None
    return round(values[KEY_VARIABEL_TARIEF] + values[KEY_BELASTING_LEIDINGWATER], 6)


def _vastrecht_per_dag(data: dict[str, Any]) -> float | None:
    vastrecht = data["values"].get(KEY_VASTRECHT)
    if vastrecht is None:
        return None
    dagen = 366 if calendar.isleap(data[ATTR_JAAR]) else 365
    return round(vastrecht / dagen, 6)


def _laatst_gecontroleerd(data: dict[str, Any]) -> datetime | None:
    value = data.get(ATTR_LAATST_GECONTROLEERD)
    return dt_util.parse_datetime(value) if value else None


@dataclass(frozen=True, kw_only=True)
class EvidesSensorDescription(SensorEntityDescription):
    """Describes an Evides tarief sensor."""

    value_fn: Callable[[dict[str, Any]], float | datetime | None]
    tariff_attributes: bool = True


SENSOR_DESCRIPTIONS: tuple[EvidesSensorDescription, ...] = (
    EvidesSensorDescription(
        key=KEY_VASTRECHT,
        translation_key="vastrecht",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=2,
        icon="mdi:cash",
        value_fn=_scraped(KEY_VASTRECHT),
    ),
    EvidesSensorDescription(
        key=KEY_VARIABEL_TARIEF,
        translation_key="variabel_tarief",
        native_unit_of_measurement=UNIT_EUR_PER_M3,
        suggested_display_precision=3,
        icon="mdi:water",
        value_fn=_scraped(KEY_VARIABEL_TARIEF),
    ),
    EvidesSensorDescription(
        key=KEY_BELASTING_LEIDINGWATER,
        translation_key="belasting_leidingwater",
        native_unit_of_measurement=UNIT_EUR_PER_M3,
        suggested_display_precision=3,
        icon="mdi:water-percent",
        value_fn=_scraped(KEY_BELASTING_LEIDINGWATER),
    ),
    EvidesSensorDescription(
        key=KEY_TOTAAL_PER_M3,
        translation_key="totaal_per_m3",
        native_unit_of_measurement=UNIT_EUR_PER_M3,
        suggested_display_precision=3,
        icon="mdi:water-plus",
        value_fn=_totaal_per_m3,
    ),
    EvidesSensorDescription(
        key=KEY_VASTRECHT_PER_DAG,
        translation_key="vastrecht_per_dag",
        native_unit_of_measurement=CURRENCY_EURO,
        device_class=SensorDeviceClass.MONETARY,
        suggested_display_precision=4,
        icon="mdi:calendar-today",
        value_fn=_vastrecht_per_dag,
    ),
    EvidesSensorDescription(
        key=KEY_LAATST_GECONTROLEERD,
        translation_key="laatst_gecontroleerd",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_laatst_gecontroleerd,
        tariff_attributes=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvidesConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Evides Tarieven sensors from a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        EvidesTariefSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class EvidesTariefSensor(CoordinatorEntity[EvidesTariefCoordinator], SensorEntity):
    """Representation of a single Evides tarief value."""

    _attr_has_entity_name = True
    # Changes on every successful check; not worth a recorder row each time.
    _unrecorded_attributes = frozenset({ATTR_LAATST_GECONTROLEERD, ATTR_BRON_URL})
    entity_description: EvidesSensorDescription

    def __init__(
        self,
        coordinator: EvidesTariefCoordinator,
        entry: EvidesConfigEntry,
        description: EvidesSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Evides Tarieven",
            manufacturer="Evides",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=TARIEVEN_URL,
        )

    @property
    def native_value(self) -> float | datetime | None:
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def available(self) -> bool:
        # A tariff that is missing from the page (layout change) is shown as
        # unavailable instead of 'unknown', so it is clearly broken.
        return super().available and self.native_value is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.entity_description.tariff_attributes:
            return None
        data = self.coordinator.data or {}
        return {
            ATTR_JAAR: data.get(ATTR_JAAR),
            ATTR_JAAR_BRON: data.get(ATTR_JAAR_BRON),
            ATTR_BRON_URL: data.get(ATTR_BRON_URL),
            ATTR_LAATST_GECONTROLEERD: data.get(ATTR_LAATST_GECONTROLEERD),
        }

"""Sensor platform for Carris integration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import BusArrivalResponse
from .const import (
    ATTRIBUTION,
    CONF_ROUTE_NUMBER,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    DOMAIN,
    MANUFACTURER,
    MODEL_BUS_STOP,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Carris sensor from a config entry."""
    _LOGGER.debug("Setting up Carris sensor for entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    config = data["config"]
    coordinator = data["arrival_coordinator"]

    stop_id: int = config[CONF_STOP_ID]
    route_number: str | None = config.get(CONF_ROUTE_NUMBER)
    stop_name: str = config.get(CONF_STOP_NAME, f"Stop {stop_id}")

    _LOGGER.debug("Carris config: stop_id=%s, route=%s, name=%s", stop_id, route_number, stop_name)

    entities: list[SensorEntity] = [
        CarrisNextBusSensor(coordinator, entry, stop_id, route_number, stop_name),
    ]

    # Add sensor for each upcoming bus if no specific route
    if not route_number:
        entities.append(CarrisAllBusesSensor(coordinator, entry, stop_id, stop_name))

    _LOGGER.info("Adding %d Carris sensor entities", len(entities))
    async_add_entities(entities, True)


class CarrisBaseSensor(
    CoordinatorEntity[DataUpdateCoordinator[list[BusArrivalResponse]]], SensorEntity
):
    """Base sensor for Carris entities."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[list[BusArrivalResponse]],
        entry: ConfigEntry,
        stop_id: int,
        stop_name: str,
    ) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._stop_id = stop_id
        self._stop_name = stop_name
        self._entry = entry

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._stop_id))},
            name=f"Carris {self._stop_name}",
            manufacturer=MANUFACTURER,
            model=MODEL_BUS_STOP,
            configuration_url="https://www.carris.pt",
            suggested_area="Transport",
        )


class CarrisNextBusSensor(CarrisBaseSensor):
    """Sensor for next bus arrival."""

    _attr_icon = "mdi:bus"
    _attr_native_unit_of_measurement = "min"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[list[BusArrivalResponse]],
        entry: ConfigEntry,
        stop_id: int,
        route_number: str | None,
        stop_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, stop_id, stop_name)
        self._route_number = route_number

        route_suffix = f"_{route_number}" if route_number else ""
        self._attr_unique_id = f"carris_{stop_id}{route_suffix}_next"

        # Entity name (device name will be prepended by HA)
        self._attr_name = f"Next {route_number}" if route_number else "Next Bus"

        _LOGGER.debug("Created sensor: %s (unique_id: %s)", self._attr_name, self._attr_unique_id)

    def _get_filtered_buses(self) -> list[BusArrivalResponse]:
        """Get buses filtered by route if applicable."""
        buses: list[BusArrivalResponse] = self.coordinator.data or []
        if self._route_number:
            buses = [b for b in buses if b.get("routeNumber") == self._route_number]
        return buses

    @property
    def native_value(self) -> int | None:
        """Return minutes until next bus."""
        buses = self._get_filtered_buses()

        if not buses:
            return None

        next_bus = buses[0]
        arrival_str = next_bus.get("stopTime")

        if not arrival_str:
            return None

        try:
            arrival = datetime.fromisoformat(arrival_str.replace("Z", "+00:00"))
            now = datetime.now(UTC)
            diff = (arrival - now).total_seconds() / 60
            return max(0, round(diff))
        except (ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        buses = self._get_filtered_buses()

        if not buses:
            return {"stop_id": self._stop_id}

        next_bus = buses[0]

        attrs: dict[str, Any] = {
            "stop_id": self._stop_id,
            "route_number": next_bus.get("routeNumber"),
            "destination": next_bus.get("destination"),
            "arrival_time": next_bus.get("stopTime"),
        }

        # Add next 5 buses
        upcoming: list[dict[str, Any]] = []
        for bus in buses[:5]:
            upcoming.append(
                {
                    "route": bus.get("routeNumber"),
                    "destination": bus.get("destination"),
                    "time": bus.get("stopTime"),
                }
            )
        attrs["upcoming_buses"] = upcoming

        return attrs


class CarrisAllBusesSensor(CarrisBaseSensor):
    """Sensor showing all upcoming buses at a stop."""

    _attr_icon = "mdi:bus-multiple"
    _attr_name = "All Buses"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[list[BusArrivalResponse]],
        entry: ConfigEntry,
        stop_id: int,
        stop_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, stop_id, stop_name)
        self._attr_unique_id = f"carris_{stop_id}_all"
        _LOGGER.debug("Created sensor: %s (unique_id: %s)", self._attr_name, self._attr_unique_id)

    @property
    def native_value(self) -> int:
        """Return number of upcoming buses."""
        return len(self.coordinator.data or [])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return all upcoming buses."""
        buses: list[BusArrivalResponse] = self.coordinator.data or []
        return {
            "stop_id": self._stop_id,
            "buses": [
                {
                    "route": b.get("routeNumber"),
                    "destination": b.get("destination"),
                    "time": b.get("stopTime"),
                }
                for b in buses
            ],
        }

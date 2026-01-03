"""Sensor platform for Carris integration."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
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

from .const import (
    DOMAIN,
    CONF_STOP_ID,
    CONF_ROUTE_NUMBER,
    CONF_STOP_NAME,
    DEFAULT_SCAN_INTERVAL,
    MANUFACTURER,
    MODEL_BUS_STOP,
    ATTRIBUTION,
)
from .api import BusArrivalResponse

_LOGGER = logging.getLogger(__name__)

# Refresh every 1 minute (60 seconds)
SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Carris sensor from a config entry."""
    _LOGGER.debug("Setting up Carris sensor for entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    client = data["client"]
    config = data["config"]

    stop_id: int = config[CONF_STOP_ID]
    route_number: str | None = config.get(CONF_ROUTE_NUMBER)
    stop_name: str = config.get(CONF_STOP_NAME, f"Stop {stop_id}")

    _LOGGER.debug("Carris config: stop_id=%s, route=%s, name=%s", stop_id, route_number, stop_name)

    async def async_update_data() -> list[BusArrivalResponse]:
        """Fetch data from API."""
        try:
            result = await client.get_next_buses(stop_id)
            _LOGGER.debug("Carris API returned %d buses", len(result) if result else 0)
            return result
        except Exception as err:
            _LOGGER.warning("Failed to fetch Carris data: %s", err, exc_info=True)
            return []

    coordinator: DataUpdateCoordinator[list[BusArrivalResponse]] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"carris_{stop_id}",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Store coordinator in hass.data for other platforms to use
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    # Don't fail if first refresh fails - just start with empty data
    await coordinator.async_refresh()
    _LOGGER.debug("Carris coordinator data: %s", coordinator.data)

    entities: list[SensorEntity] = [
        CarrisNextBusSensor(coordinator, entry, stop_id, route_number, stop_name),
    ]

    # Add sensor for each upcoming bus if no specific route
    if not route_number:
        entities.append(CarrisAllBusesSensor(coordinator, entry, stop_id, stop_name))

    _LOGGER.info("Adding %d Carris entities", len(entities))
    async_add_entities(entities, True)


class CarrisBaseSensor(CoordinatorEntity[DataUpdateCoordinator[list[BusArrivalResponse]]], SensorEntity):
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
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._stop_id))},
            name=f"Carris {self._stop_name}",
            manufacturer=MANUFACTURER,
            model=MODEL_BUS_STOP,
            configuration_url="https://www.carris.pt",
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
            now = datetime.now(timezone.utc)
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
            upcoming.append({
                "route": bus.get("routeNumber"),
                "destination": bus.get("destination"),
                "time": bus.get("stopTime"),
            })
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

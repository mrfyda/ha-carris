"""Binary sensor platform for Carris integration."""
from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
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
    ATTRIBUTION,
    CONF_ARRIVAL_THRESHOLD,
    CONF_ROUTE_NUMBER,
    CONF_STOP_ID,
    CONF_STOP_NAME,
    DEFAULT_ARRIVAL_THRESHOLD,
    DOMAIN,
    MANUFACTURER,
    MODEL_BUS_STOP,
)
from .api import BusArrivalResponse

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Carris binary sensor from a config entry."""
    _LOGGER.debug("Setting up Carris binary sensor for entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    config = data["config"]
    coordinator = data["arrival_coordinator"]

    stop_id: int = config[CONF_STOP_ID]
    route_number: str | None = config.get(CONF_ROUTE_NUMBER)
    stop_name: str = config.get(CONF_STOP_NAME, f"Stop {stop_id}")

    entities: list[BinarySensorEntity] = [
        CarrisBusArrivingSoonSensor(
            coordinator, entry, stop_id, route_number, stop_name
        ),
    ]

    _LOGGER.info("Adding %d Carris binary sensor entities", len(entities))
    async_add_entities(entities, True)


class CarrisBusArrivingSoonSensor(
    CoordinatorEntity[DataUpdateCoordinator[list[BusArrivalResponse]]],
    BinarySensorEntity,
):
    """Binary sensor that turns on when a bus is arriving soon."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[list[BusArrivalResponse]],
        entry: ConfigEntry,
        stop_id: int,
        route_number: str | None,
        stop_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._stop_id = stop_id
        self._route_number = route_number
        self._stop_name = stop_name
        self._entry = entry
        # Get threshold from options or use default
        self._threshold = entry.options.get(CONF_ARRIVAL_THRESHOLD, DEFAULT_ARRIVAL_THRESHOLD)

        route_suffix = f"_{route_number}" if route_number else ""
        self._attr_unique_id = f"carris_{stop_id}{route_suffix}_arriving_soon"
        self._attr_name = f"{route_number} Arriving Soon" if route_number else "Bus Arriving Soon"

        _LOGGER.debug(
            "Created binary sensor: %s (unique_id: %s)",
            self._attr_name,
            self._attr_unique_id,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Return the icon based on state."""
        return "mdi:bus-clock" if self.is_on else "mdi:bus"

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

    def _get_minutes_to_next_bus(self) -> int | None:
        """Get minutes until next bus."""
        buses: list[BusArrivalResponse] = self.coordinator.data or []

        if self._route_number:
            buses = [b for b in buses if b.get("routeNumber") == self._route_number]

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
    def is_on(self) -> bool:
        """Return true if bus is arriving within threshold."""
        minutes = self._get_minutes_to_next_bus()
        if minutes is None:
            return False
        return minutes <= self._threshold

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        minutes = self._get_minutes_to_next_bus()
        buses: list[BusArrivalResponse] = self.coordinator.data or []

        if self._route_number:
            buses = [b for b in buses if b.get("routeNumber") == self._route_number]

        attrs: dict[str, Any] = {
            "stop_id": self._stop_id,
            "threshold_minutes": self._threshold,
            "minutes_to_arrival": minutes,
        }

        if buses:
            next_bus = buses[0]
            attrs["next_route"] = next_bus.get("routeNumber")
            attrs["next_destination"] = next_bus.get("destination")
            attrs["next_arrival_time"] = next_bus.get("stopTime")

        return attrs


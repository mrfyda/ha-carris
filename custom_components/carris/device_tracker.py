"""Device tracker platform for Carris integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
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
    CONF_STOP_LAT,
    CONF_STOP_LNG,
    DEFAULT_SCAN_INTERVAL,
    MANUFACTURER,
    ATTRIBUTION,
)
from .api import BusSnapshotItem, CarrisApiClient

_LOGGER = logging.getLogger(__name__)

# Refresh bus positions slightly more frequently
BUS_SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL // 2)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Carris device tracker from a config entry."""
    _LOGGER.debug("Setting up Carris device tracker for entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    client: CarrisApiClient = data["client"]
    config = data["config"]

    stop_id: int = config[CONF_STOP_ID]
    route_number: str | None = config.get(CONF_ROUTE_NUMBER)
    stop_name: str = config.get(CONF_STOP_NAME, f"Stop {stop_id}")
    stop_lat: float | None = config.get(CONF_STOP_LAT)
    stop_lng: float | None = config.get(CONF_STOP_LNG)

    # Only create device tracker if a specific route is configured
    if not route_number:
        _LOGGER.debug("No specific route configured, skipping device tracker")
        return

    # Detect the correct direction for this stop/route combination
    direction = await client.get_direction_for_stop(route_number, stop_id)
    if direction:
        _LOGGER.info(
            "Detected direction %d for route %s at stop %d",
            direction, route_number, stop_id
        )
    else:
        _LOGGER.warning(
            "Could not detect direction for route %s at stop %d, showing all buses",
            route_number, stop_id
        )

    async def async_update_bus_positions() -> list[BusSnapshotItem]:
        """Fetch bus positions from API."""
        try:
            result = await client.get_buses_for_route(route_number, direction)
            _LOGGER.debug(
                "Carris API returned %d buses for route %s (direction %s)",
                len(result) if result else 0,
                route_number,
                direction,
            )
            return result
        except Exception as err:
            _LOGGER.warning(
                "Failed to fetch Carris bus positions: %s", err, exc_info=True
            )
            return []

    bus_coordinator: DataUpdateCoordinator[list[BusSnapshotItem]] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"carris_{stop_id}_{route_number}_buses",
        update_method=async_update_bus_positions,
        update_interval=BUS_SCAN_INTERVAL,
    )

    # Store coordinator for potential future use
    hass.data[DOMAIN][entry.entry_id]["bus_coordinator"] = bus_coordinator

    # Initial refresh
    await bus_coordinator.async_refresh()

    entities: list[TrackerEntity] = [
        CarrisBusTracker(
            bus_coordinator,
            entry,
            stop_id,
            route_number,
            stop_name,
            stop_lat,
            stop_lng,
        ),
    ]

    _LOGGER.info("Adding %d Carris device tracker entities", len(entities))
    async_add_entities(entities, True)


class CarrisBusTracker(
    CoordinatorEntity[DataUpdateCoordinator[list[BusSnapshotItem]]],
    TrackerEntity,
):
    """Device tracker for the next arriving bus."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[list[BusSnapshotItem]],
        entry: ConfigEntry,
        stop_id: int,
        route_number: str,
        stop_name: str,
        stop_lat: float | None,
        stop_lng: float | None,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._stop_id = stop_id
        self._route_number = route_number
        self._stop_name = stop_name
        self._stop_lat = stop_lat
        self._stop_lng = stop_lng
        self._entry = entry

        self._attr_unique_id = f"carris_{stop_id}_{route_number}_bus_location"
        self._attr_name = f"Bus {route_number}"
        self._attr_icon = "mdi:bus"

        _LOGGER.debug(
            "Created device tracker: %s (unique_id: %s)",
            self._attr_name,
            self._attr_unique_id,
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._stop_id))},
            name=f"Carris {self._stop_name}",
            manufacturer=MANUFACTURER,
            model="Bus",
            configuration_url="https://www.carris.pt",
        )

    @property
    def source_type(self) -> SourceType:
        """Return the source type."""
        return SourceType.GPS

    def _get_bus_coordinates(self, bus: BusSnapshotItem) -> tuple[float | None, float | None]:
        """Extract coordinates from a bus object.
        
        The Carris API returns coordinates in a 'path' array where each item
        has 'lat' and 'lng' fields. We use the first (most recent) position.
        """
        # The Carris API uses a 'path' array with position history
        path = bus.get("path", [])
        if isinstance(path, list) and len(path) > 0:
            first_pos = path[0]
            if isinstance(first_pos, dict):
                lat = first_pos.get("lat")
                lng = first_pos.get("lng")
                if lat is not None and lng is not None:
                    return (float(lat), float(lng))
        
        # Fallback: try nested location object
        location = bus.get("location", {})
        if isinstance(location, dict) and location:
            lat = location.get("lat") or location.get("latitude")
            lng = location.get("lng") or location.get("longitude")
            if lat is not None and lng is not None:
                return (float(lat), float(lng))
        
        # Fallback: try flat structure
        lat = bus.get("lat") or bus.get("latitude")
        lng = bus.get("lng") or bus.get("longitude")
        if lat is not None and lng is not None:
            return (float(lat), float(lng))
        
        return (None, None)

    def _get_nearest_bus(self) -> BusSnapshotItem | None:
        """Get the nearest bus on the route."""
        buses: list[BusSnapshotItem] = self.coordinator.data or []
        
        if not buses:
            return None

        # Filter buses that have valid coordinates
        buses_with_coords = [
            (bus, self._get_bus_coordinates(bus))
            for bus in buses
        ]
        buses_with_coords = [
            (bus, coords) for bus, coords in buses_with_coords
            if coords[0] is not None and coords[1] is not None
        ]
        
        if not buses_with_coords:
            _LOGGER.debug("No buses with valid coordinates found")
            return buses[0] if buses else None

        # If we have stop coordinates, find the nearest bus
        if self._stop_lat is not None and self._stop_lng is not None:
            def distance_to_stop(item: tuple[BusSnapshotItem, tuple[float | None, float | None]]) -> float:
                _, coords = item
                bus_lat, bus_lng = coords
                if bus_lat is None or bus_lng is None:
                    return float('inf')
                # Simple Euclidean distance (good enough for nearby buses)
                return ((bus_lat - self._stop_lat) ** 2 + (bus_lng - self._stop_lng) ** 2) ** 0.5

            # Sort by distance and return nearest
            sorted_buses = sorted(buses_with_coords, key=distance_to_stop)
            return sorted_buses[0][0] if sorted_buses else None

        # Otherwise just return the first bus with coordinates
        return buses_with_coords[0][0] if buses_with_coords else None

    @property
    def latitude(self) -> float | None:
        """Return latitude of the bus."""
        bus = self._get_nearest_bus()
        if bus is None:
            # Fallback to stop location if no bus found
            return self._stop_lat
        
        lat, _ = self._get_bus_coordinates(bus)
        return lat if lat is not None else self._stop_lat

    @property
    def longitude(self) -> float | None:
        """Return longitude of the bus."""
        bus = self._get_nearest_bus()
        if bus is None:
            # Fallback to stop location if no bus found
            return self._stop_lng
        
        _, lng = self._get_bus_coordinates(bus)
        return lng if lng is not None else self._stop_lng

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy."""
        # GPS accuracy in meters
        return 50

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        bus = self._get_nearest_bus()
        buses: list[BusSnapshotItem] = self.coordinator.data or []

        attrs: dict[str, Any] = {
            "stop_id": self._stop_id,
            "route_number": self._route_number,
            "buses_on_route": len(buses),
        }

        if bus:
            lat, lng = self._get_bus_coordinates(bus)
            attrs["bus_lat"] = lat
            attrs["bus_lng"] = lng
            attrs["vehicle_id"] = bus.get("id")
            attrs["plate"] = bus.get("plate")
            attrs["direction"] = bus.get("direction")

        if self._stop_lat is not None and self._stop_lng is not None:
            attrs["stop_lat"] = self._stop_lat
            attrs["stop_lng"] = self._stop_lng

        return attrs


"""Device tracker platform for Carris integration."""

from __future__ import annotations

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

from .api import BusArrivalResponse, BusSnapshotItem
from .const import (
    ATTRIBUTION,
    CONF_ROUTE_NUMBER,
    CONF_ROUTES,
    CONF_STOP_ID,
    CONF_STOP_LAT,
    CONF_STOP_LNG,
    CONF_STOP_NAME,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Carris device tracker from a config entry."""
    _LOGGER.debug("Setting up Carris device tracker for entry: %s", entry.entry_id)

    data = hass.data[DOMAIN][entry.entry_id]
    config = data["config"]
    bus_coordinator = data.get("bus_coordinator")
    arrival_coordinator = data.get("arrival_coordinator")
    direction: int | None = data.get("direction")
    directions: dict[str, int] = data.get("directions", {})

    stop_id: int = config[CONF_STOP_ID]
    route_number: str | None = config.get(CONF_ROUTE_NUMBER)
    routes: list[str] = config.get(CONF_ROUTES, [])
    stop_name: str = config.get(CONF_STOP_NAME, f"Stop {stop_id}")
    stop_lat: float | None = config.get(CONF_STOP_LAT)
    stop_lng: float | None = config.get(CONF_STOP_LNG)

    # Skip if no bus coordinator available
    if bus_coordinator is None:
        _LOGGER.debug("No bus coordinator available, skipping device tracker")
        return

    entities: list[TrackerEntity] = []

    if route_number:
        # Single route mode: create one tracker for the specified route
        entities.append(
            CarrisBusTracker(
                bus_coordinator,
                arrival_coordinator,
                entry,
                stop_id,
                route_number,
                stop_name,
                stop_lat,
                stop_lng,
                direction,
            )
        )
    elif routes:
        # All routes mode: create one tracker per route that serves the stop
        _LOGGER.debug("Creating device trackers for %d routes at stop %s", len(routes), stop_id)
        for route in routes:
            route_direction = directions.get(route)
            entities.append(
                CarrisBusTracker(
                    bus_coordinator,
                    arrival_coordinator,
                    entry,
                    stop_id,
                    route,
                    stop_name,
                    stop_lat,
                    stop_lng,
                    route_direction,
                )
            )

    if not entities:
        _LOGGER.debug("No routes configured, skipping device tracker")
        return

    _LOGGER.info("Adding %d Carris device tracker entities", len(entities))
    async_add_entities(entities, True)


class CarrisBusTracker(
    CoordinatorEntity[DataUpdateCoordinator[list[BusSnapshotItem]]],
    TrackerEntity,
):
    """Device tracker for the next arriving bus."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[list[BusSnapshotItem]],
        arrival_coordinator: DataUpdateCoordinator[list[BusArrivalResponse]] | None,
        entry: ConfigEntry,
        stop_id: int,
        route_number: str,
        stop_name: str,
        stop_lat: float | None,
        stop_lng: float | None,
        direction: int | None = None,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._arrival_coordinator = arrival_coordinator
        self._stop_id = stop_id
        self._route_number = route_number
        self._stop_name = stop_name
        self._stop_lat = stop_lat
        self._stop_lng = stop_lng
        self._direction = direction
        self._entry = entry

        self._attr_unique_id = f"carris_{stop_id}_{route_number}_bus_location"
        # Use just the route number as name so it shows on the map marker
        self._attr_name = route_number
        self._attr_icon = "mdi:bus"
        # Disable has_entity_name so the name isn't prefixed with device name
        self._attr_has_entity_name = False
        # Generate SVG badge with route number for map display
        self._attr_entity_picture = self._generate_route_badge(route_number)

        _LOGGER.debug(
            "Created device tracker: %s (unique_id: %s)",
            self._attr_name,
            self._attr_unique_id,
        )

    @staticmethod
    def _generate_route_badge(route_number: str) -> str:
        """Generate an SVG data URL with the route number for map display."""
        import base64

        # Adjust font size based on route number length
        if len(route_number) <= 2:
            font_size = 16
        elif len(route_number) == 3:
            font_size = 13
        else:
            font_size = 10

        # Carris brand colors: yellow background, blue text
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">'
            f'<circle cx="20" cy="20" r="18" fill="#FFCC00" stroke="#003366" stroke-width="2"/>'
            f'<text x="20" y="25" text-anchor="middle" fill="#003366" '
            f'font-family="Arial,sans-serif" font-size="{font_size}" font-weight="bold">'
            f"{route_number}</text></svg>"
        )
        encoded = base64.b64encode(svg.encode()).decode()
        return f"data:image/svg+xml;base64,{encoded}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    def _has_pending_arrivals(self) -> bool:
        """Check if there are pending arrivals for this route at this stop.

        This helps filter out buses that have already passed the stop.
        If no arrival data is available, assume buses might still be coming.
        """
        if self._arrival_coordinator is None:
            return True  # No arrival data, assume buses might be coming

        arrivals: list[BusArrivalResponse] = self._arrival_coordinator.data or []

        # Check if any arrivals are for this route
        route_arrivals = [a for a in arrivals if a.get("routeNumber") == self._route_number]

        if route_arrivals:
            _LOGGER.debug(
                "Found %d pending arrivals for route %s at stop %s",
                len(route_arrivals),
                self._route_number,
                self._stop_id,
            )
            return True

        _LOGGER.debug(
            "No pending arrivals for route %s at stop %s - bus may have passed",
            self._route_number,
            self._stop_id,
        )
        return False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._stop_id))},
            name=f"Carris {self._stop_name}",
            manufacturer=MANUFACTURER,
            model="Bus",
            configuration_url="https://www.carris.pt",
            suggested_area="Transport",
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
            loc_lat = location.get("lat") or location.get("latitude")
            loc_lng = location.get("lng") or location.get("longitude")
            if loc_lat is not None and loc_lng is not None:
                return (float(loc_lat), float(loc_lng))

        # Fallback: try flat structure
        flat_lat = bus.get("lat") or bus.get("latitude")
        flat_lng = bus.get("lng") or bus.get("longitude")
        if flat_lat is not None and flat_lng is not None:
            try:
                return (float(flat_lat), float(flat_lng))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                pass

        return (None, None)

    def _get_nearest_bus(self) -> BusSnapshotItem | None:
        """Get the nearest bus on the route heading toward this stop."""
        buses: list[BusSnapshotItem] = self.coordinator.data or []

        if not buses:
            return None

        # Filter buses by route number (important when coordinator has all buses)
        buses = [bus for bus in buses if bus.get("route") == self._route_number]

        if not buses:
            return None

        # Filter by direction if known (only show buses heading toward this stop)
        if self._direction is not None:
            buses = [bus for bus in buses if bus.get("direction") == self._direction]

        if not buses:
            return None

        # Filter buses that have valid coordinates
        buses_with_coords = [(bus, self._get_bus_coordinates(bus)) for bus in buses]
        buses_with_coords = [
            (bus, coords)
            for bus, coords in buses_with_coords
            if coords[0] is not None and coords[1] is not None
        ]

        if not buses_with_coords:
            _LOGGER.debug("No buses with valid coordinates found")
            return buses[0] if buses else None

        # If we have stop coordinates, find the nearest bus
        if self._stop_lat is not None and self._stop_lng is not None:
            stop_lat = self._stop_lat
            stop_lng = self._stop_lng

            def distance_to_stop(
                item: tuple[BusSnapshotItem, tuple[float | None, float | None]],
            ) -> float:
                _, coords = item
                bus_lat, bus_lng = coords
                if bus_lat is None or bus_lng is None:
                    return float("inf")
                # Simple Euclidean distance (good enough for nearby buses)
                return ((bus_lat - stop_lat) ** 2 + (bus_lng - stop_lng) ** 2) ** 0.5

            # Sort by distance and return nearest
            sorted_buses = sorted(buses_with_coords, key=distance_to_stop)
            return sorted_buses[0][0] if sorted_buses else None

        # Otherwise just return the first bus with coordinates
        return buses_with_coords[0][0] if buses_with_coords else None

    @property
    def latitude(self) -> float | None:
        """Return latitude of the bus."""
        # Don't show bus location if it has already passed the stop
        if not self._has_pending_arrivals():
            return None

        bus = self._get_nearest_bus()
        if bus is None:
            return None

        lat, _ = self._get_bus_coordinates(bus)
        return lat

    @property
    def longitude(self) -> float | None:
        """Return longitude of the bus."""
        # Don't show bus location if it has already passed the stop
        if not self._has_pending_arrivals():
            return None

        bus = self._get_nearest_bus()
        if bus is None:
            return None

        _, lng = self._get_bus_coordinates(bus)
        return lng

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy."""
        # GPS accuracy in meters
        return 50

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        bus = self._get_nearest_bus()
        all_buses: list[BusSnapshotItem] = self.coordinator.data or []
        # Filter buses by route for accurate count
        buses_on_route = [b for b in all_buses if b.get("route") == self._route_number]
        # Also filter by direction if known
        if self._direction is not None:
            buses_on_route = [b for b in buses_on_route if b.get("direction") == self._direction]

        attrs: dict[str, Any] = {
            "stop_id": self._stop_id,
            "route_number": self._route_number,
            "buses_on_route": len(buses_on_route),
            "direction": self._direction,
        }

        if bus:
            lat, lng = self._get_bus_coordinates(bus)
            attrs["bus_lat"] = lat
            attrs["bus_lng"] = lng
            attrs["vehicle_id"] = bus.get("id")
            attrs["plate"] = bus.get("plate")

        if self._stop_lat is not None and self._stop_lng is not None:
            attrs["stop_lat"] = self._stop_lat
            attrs["stop_lng"] = self._stop_lng

        return attrs

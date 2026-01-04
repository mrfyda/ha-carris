"""Tests for the Carris device tracker platform."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.components.device_tracker import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.carris.device_tracker import CarrisBusTracker
from custom_components.carris.const import DOMAIN


class TestCarrisBusTracker:
    """Test suite for CarrisBusTracker."""

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Create a mock config entry."""
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry_id"
        return entry

    @pytest.fixture
    def mock_coordinator(
        self, mock_bus_snapshot: list[dict[str, Any]]
    ) -> MagicMock:
        """Create a mock coordinator."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = mock_bus_snapshot
        return coordinator

    def test_tracker_name(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test tracker name."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        assert tracker.name == "Bus 742"
        assert tracker.unique_id == "carris_9804_742_bus_location"

    def test_source_type_is_gps(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test source type is GPS."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        assert tracker.source_type == SourceType.GPS

    def test_latitude_returns_bus_location(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test latitude returns bus location."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        # Should return the nearest bus's latitude
        assert tracker.latitude is not None
        assert isinstance(tracker.latitude, float)

    def test_longitude_returns_bus_location(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test longitude returns bus location."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        # Should return the nearest bus's longitude
        assert tracker.longitude is not None
        assert isinstance(tracker.longitude, float)

    def test_latitude_fallback_to_stop_when_no_buses(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test latitude falls back to stop location when no buses."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = []

        tracker = CarrisBusTracker(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        assert tracker.latitude == 38.7244087
        assert tracker.longitude == -9.1173888

    def test_get_bus_coordinates_from_path(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test extracting coordinates from bus path."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        bus = mock_coordinator.data[0]
        lat, lng = tracker._get_bus_coordinates(bus)

        assert lat == 38.7250
        assert lng == -9.1180

    def test_get_bus_coordinates_empty_path(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test handling empty path."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        bus = {"route": "742", "path": []}
        lat, lng = tracker._get_bus_coordinates(bus)

        assert lat is None
        assert lng is None

    def test_get_nearest_bus(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test getting nearest bus to stop."""
        # Create buses at different distances
        buses = [
            {
                "route": "742",
                "id": 1,
                "path": [{"lat": 38.73, "lng": -9.12}],  # Further
            },
            {
                "route": "742",
                "id": 2,
                "path": [{"lat": 38.7245, "lng": -9.1174}],  # Closer
            },
        ]

        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = buses

        tracker = CarrisBusTracker(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        nearest = tracker._get_nearest_bus()

        assert nearest is not None
        assert nearest["id"] == 2  # The closer bus

    def test_location_accuracy(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test location accuracy."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        assert tracker.location_accuracy == 50

    def test_extra_state_attributes(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test extra state attributes."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        attrs = tracker.extra_state_attributes

        assert attrs["stop_id"] == 9804
        assert attrs["route_number"] == "742"
        assert attrs["buses_on_route"] == 2
        assert "bus_lat" in attrs
        assert "bus_lng" in attrs
        assert "stop_lat" in attrs
        assert "stop_lng" in attrs

    def test_device_info(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test device info."""
        tracker = CarrisBusTracker(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
            stop_lat=38.7244087,
            stop_lng=-9.1173888,
        )

        device_info = tracker.device_info

        assert (DOMAIN, "9804") in device_info["identifiers"]
        assert device_info["name"] == "Carris R. D. Fuas Roupinho"
        assert device_info["manufacturer"] == "Carris"


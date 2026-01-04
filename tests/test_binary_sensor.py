"""Tests for the Carris binary sensor platform."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.carris.binary_sensor import CarrisBusArrivingSoonSensor
from custom_components.carris.const import DEFAULT_ARRIVAL_THRESHOLD, DOMAIN


class TestCarrisBusArrivingSoonSensor:
    """Test suite for CarrisBusArrivingSoonSensor."""

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Create a mock config entry."""
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry_id"
        return entry

    def test_sensor_name_with_route(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor name with specific route."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = []

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.name == "742 Arriving Soon"
        assert sensor.unique_id == "carris_9804_742_arriving_soon"

    def test_sensor_name_without_route(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor name without specific route."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = []

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number=None,
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.name == "Bus Arriving Soon"
        assert sensor.unique_id == "carris_9804_arriving_soon"

    def test_is_on_when_bus_arriving_soon(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test is_on is True when bus is arriving within threshold."""
        # Bus arriving in 3 minutes (within 5 minute threshold)
        future_time = datetime.now(timezone.utc) + timedelta(minutes=3)
        buses = [
            {
                "routeNumber": "742",
                "stopId": 9804,
                "stopTime": future_time.isoformat(),
                "destination": "Pólo Univ. Ajuda",
            }
        ]

        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = buses

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.is_on is True

    def test_is_off_when_bus_not_arriving_soon(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test is_on is False when bus is not arriving within threshold."""
        # Bus arriving in 10 minutes (outside 5 minute threshold)
        future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        buses = [
            {
                "routeNumber": "742",
                "stopId": 9804,
                "stopTime": future_time.isoformat(),
                "destination": "Pólo Univ. Ajuda",
            }
        ]

        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = buses

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.is_on is False

    def test_is_off_when_no_buses(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test is_on is False when no buses."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = []

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.is_on is False

    def test_filters_by_route(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor filters by route number."""
        # 728 arriving in 2 minutes, 742 arriving in 10 minutes
        soon_time = datetime.now(timezone.utc) + timedelta(minutes=2)
        later_time = datetime.now(timezone.utc) + timedelta(minutes=10)
        buses = [
            {
                "routeNumber": "728",
                "stopId": 9804,
                "stopTime": soon_time.isoformat(),
                "destination": "Other",
            },
            {
                "routeNumber": "742",
                "stopId": 9804,
                "stopTime": later_time.isoformat(),
                "destination": "Pólo Univ. Ajuda",
            },
        ]

        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = buses

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        # 742 is arriving in 10 minutes, so should be False
        assert sensor.is_on is False

    def test_icon_changes_based_on_state(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test icon changes based on state."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = []

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        # When off
        assert sensor.icon == "mdi:bus"

        # When on
        soon_time = datetime.now(timezone.utc) + timedelta(minutes=2)
        coordinator.data = [
            {
                "routeNumber": "742",
                "stopId": 9804,
                "stopTime": soon_time.isoformat(),
                "destination": "Pólo Univ. Ajuda",
            }
        ]

        assert sensor.icon == "mdi:bus-clock"

    def test_extra_state_attributes(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test extra state attributes."""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=3)
        buses = [
            {
                "routeNumber": "742",
                "stopId": 9804,
                "stopTime": future_time.isoformat(),
                "destination": "Pólo Univ. Ajuda",
            }
        ]

        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = buses

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        attrs = sensor.extra_state_attributes

        assert attrs["stop_id"] == 9804
        assert attrs["threshold_minutes"] == DEFAULT_ARRIVAL_THRESHOLD
        assert attrs["minutes_to_arrival"] is not None
        assert attrs["next_route"] == "742"
        assert attrs["next_destination"] == "Pólo Univ. Ajuda"

    def test_device_info(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test device info."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = []

        sensor = CarrisBusArrivingSoonSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        device_info = sensor.device_info

        assert (DOMAIN, "9804") in device_info["identifiers"]
        assert device_info["name"] == "Carris R. D. Fuas Roupinho"
        assert device_info["manufacturer"] == "Carris"


"""Tests for the Carris sensor platform."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from custom_components.carris.const import DOMAIN
from custom_components.carris.sensor import (
    CarrisAllBusesSensor,
    CarrisNextBusSensor,
)


class TestCarrisNextBusSensor:
    """Test suite for CarrisNextBusSensor."""

    @pytest.fixture
    def mock_coordinator(
        self, mock_next_buses: list[dict[str, Any]]
    ) -> MagicMock:
        """Create a mock coordinator."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = mock_next_buses
        return coordinator

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Create a mock config entry."""
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry_id"
        return entry

    def test_sensor_name_with_route(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor name with specific route."""
        sensor = CarrisNextBusSensor(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.name == "Next 742"
        assert sensor.unique_id == "carris_9804_742_next"

    def test_sensor_name_without_route(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor name without specific route."""
        sensor = CarrisNextBusSensor(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number=None,
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.name == "Next Bus"
        assert sensor.unique_id == "carris_9804_next"

    def test_sensor_filters_by_route(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor filters buses by route."""
        sensor = CarrisNextBusSensor(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        filtered = sensor._get_filtered_buses()
        assert len(filtered) == 2
        assert all(bus["routeNumber"] == "742" for bus in filtered)

    def test_sensor_native_value_returns_minutes(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test native value returns minutes until arrival."""
        # Create bus arriving in 10 minutes
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

        sensor = CarrisNextBusSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        # Should be approximately 10 minutes
        assert sensor.native_value is not None
        assert 9 <= sensor.native_value <= 11

    def test_sensor_native_value_returns_zero_for_past(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test native value returns 0 for past arrivals."""
        # Create bus that arrived 5 minutes ago
        past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        buses = [
            {
                "routeNumber": "742",
                "stopId": 9804,
                "stopTime": past_time.isoformat(),
                "destination": "Pólo Univ. Ajuda",
            }
        ]

        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = buses

        sensor = CarrisNextBusSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.native_value == 0

    def test_sensor_native_value_returns_none_no_buses(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test native value returns None when no buses."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = []

        sensor = CarrisNextBusSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.native_value is None

    def test_sensor_extra_state_attributes(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test extra state attributes."""
        sensor = CarrisNextBusSensor(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        attrs = sensor.extra_state_attributes

        assert attrs["stop_id"] == 9804
        assert attrs["route_number"] == "742"
        assert attrs["destination"] == "Pólo Univ. Ajuda"
        assert "upcoming_buses" in attrs
        assert len(attrs["upcoming_buses"]) <= 5

    def test_sensor_device_info(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test device info."""
        sensor = CarrisNextBusSensor(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            route_number="742",
            stop_name="R. D. Fuas Roupinho",
        )

        device_info = sensor.device_info

        assert (DOMAIN, "9804") in device_info["identifiers"]
        assert device_info["name"] == "Carris R. D. Fuas Roupinho"
        assert device_info["manufacturer"] == "Carris"


class TestCarrisAllBusesSensor:
    """Test suite for CarrisAllBusesSensor."""

    @pytest.fixture
    def mock_coordinator(
        self, mock_next_buses: list[dict[str, Any]]
    ) -> MagicMock:
        """Create a mock coordinator."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = mock_next_buses
        return coordinator

    @pytest.fixture
    def mock_entry(self) -> MagicMock:
        """Create a mock config entry."""
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry_id"
        return entry

    def test_sensor_name(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test sensor name."""
        sensor = CarrisAllBusesSensor(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.name == "All Buses"
        assert sensor.unique_id == "carris_9804_all"

    def test_sensor_native_value_returns_count(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test native value returns bus count."""
        sensor = CarrisAllBusesSensor(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.native_value == 3

    def test_sensor_native_value_returns_zero_no_buses(
        self,
        mock_entry: MagicMock,
    ) -> None:
        """Test native value returns 0 when no buses."""
        coordinator = MagicMock(spec=DataUpdateCoordinator)
        coordinator.data = []

        sensor = CarrisAllBusesSensor(
            coordinator=coordinator,
            entry=mock_entry,
            stop_id=9804,
            stop_name="R. D. Fuas Roupinho",
        )

        assert sensor.native_value == 0

    def test_sensor_extra_state_attributes(
        self,
        mock_coordinator: MagicMock,
        mock_entry: MagicMock,
    ) -> None:
        """Test extra state attributes."""
        sensor = CarrisAllBusesSensor(
            coordinator=mock_coordinator,
            entry=mock_entry,
            stop_id=9804,
            stop_name="R. D. Fuas Roupinho",
        )

        attrs = sensor.extra_state_attributes

        assert attrs["stop_id"] == 9804
        assert "buses" in attrs
        assert len(attrs["buses"]) == 3


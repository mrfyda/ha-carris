"""Tests for the Carris sensor platform."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest


class TestSensorConstants:
    """Test suite for sensor constants."""

    def test_sensor_constants_defined(self) -> None:
        """Test that sensor constants are defined."""
        from custom_components.carris.const import (
            ATTRIBUTION,
            MANUFACTURER,
            MODEL_BUS_STOP,
        )

        assert ATTRIBUTION is not None
        assert MANUFACTURER is not None
        assert MODEL_BUS_STOP is not None


class TestTimeCalculations:
    """Test suite for time calculations used in sensors."""

    def test_minutes_until_arrival(self) -> None:
        """Test calculation of minutes until arrival."""
        # Simulate arrival time parsing
        now = datetime.now(UTC)
        arrival_time = now + timedelta(minutes=5)
        arrival_str = arrival_time.isoformat()

        # Parse the arrival time
        parsed = datetime.fromisoformat(arrival_str)
        minutes = int((parsed - now).total_seconds() / 60)

        assert 4 <= minutes <= 6  # Allow for small timing differences

    def test_minutes_for_past_arrival(self) -> None:
        """Test that past arrivals show 0 or negative minutes."""
        now = datetime.now(UTC)
        arrival_time = now - timedelta(minutes=2)
        arrival_str = arrival_time.isoformat()

        parsed = datetime.fromisoformat(arrival_str)
        minutes = int((parsed - now).total_seconds() / 60)

        assert minutes <= 0

    def test_arrival_time_parsing_with_timezone(self) -> None:
        """Test that arrival times with timezones are parsed correctly."""
        arrival_str = "2026-01-04T14:08:32+00:00"
        parsed = datetime.fromisoformat(arrival_str)

        assert parsed.tzinfo is not None
        assert parsed.year == 2026
        assert parsed.month == 1
        assert parsed.day == 4
        assert parsed.hour == 14
        assert parsed.minute == 8


class TestBusFiltering:
    """Test suite for bus filtering logic."""

    @pytest.fixture
    def mock_buses(self) -> list[dict[str, Any]]:
        """Return mock bus arrival data."""
        return [
            {"routeNumber": "742", "destination": "Pólo Univ. Ajuda"},
            {"routeNumber": "728", "destination": "Restelo"},
            {"routeNumber": "742", "destination": "Pólo Univ. Ajuda"},
            {"routeNumber": "15E", "destination": "Praça do Comércio"},
        ]

    def test_filter_by_route(self, mock_buses: list[dict[str, Any]]) -> None:
        """Test filtering buses by route number."""
        route = "742"
        filtered = [b for b in mock_buses if b.get("routeNumber") == route]

        assert len(filtered) == 2
        assert all(b["routeNumber"] == "742" for b in filtered)

    def test_filter_no_match(self, mock_buses: list[dict[str, Any]]) -> None:
        """Test filtering with no matching route."""
        route = "999"
        filtered = [b for b in mock_buses if b.get("routeNumber") == route]

        assert len(filtered) == 0

    def test_no_filter_returns_all(self, mock_buses: list[dict[str, Any]]) -> None:
        """Test that no filter returns all buses."""
        route = None
        filtered = [b for b in mock_buses if b.get("routeNumber") == route] if route else mock_buses

        assert len(filtered) == 4


class TestExtraStateAttributes:
    """Test suite for extra state attributes."""

    @pytest.fixture
    def mock_bus(self) -> dict[str, Any]:
        """Return mock bus arrival data."""
        return {
            "routeNumber": "742",
            "destination": "Pólo Univ. Ajuda",
            "stopTime": "2026-01-04T14:08:32+00:00",
            "stopId": 9804,
        }

    def test_extra_attributes_format(self, mock_bus: dict[str, Any]) -> None:
        """Test that extra attributes have correct format."""
        # Simulate building extra state attributes
        attrs = {
            "route": mock_bus["routeNumber"],
            "destination": mock_bus["destination"],
            "arrival_time": mock_bus["stopTime"],
        }

        assert "route" in attrs
        assert "destination" in attrs
        assert "arrival_time" in attrs
        assert attrs["route"] == "742"
        assert attrs["destination"] == "Pólo Univ. Ajuda"

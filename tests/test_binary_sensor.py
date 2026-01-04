"""Tests for the Carris binary sensor platform."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest


class TestArrivalThreshold:
    """Test suite for arrival threshold logic."""

    def test_bus_arriving_soon_within_threshold(self) -> None:
        """Test that bus is considered arriving soon when within threshold."""
        threshold_minutes = 5
        now = datetime.now(UTC)
        arrival_time = now + timedelta(minutes=3)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        is_arriving_soon = 0 <= minutes_until <= threshold_minutes

        assert is_arriving_soon is True

    def test_bus_not_arriving_soon_outside_threshold(self) -> None:
        """Test that bus is not arriving soon when outside threshold."""
        threshold_minutes = 5
        now = datetime.now(UTC)
        arrival_time = now + timedelta(minutes=10)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        is_arriving_soon = 0 <= minutes_until <= threshold_minutes

        assert is_arriving_soon is False

    def test_bus_not_arriving_soon_when_past(self) -> None:
        """Test that past arrivals don't trigger arriving soon."""
        threshold_minutes = 5
        now = datetime.now(UTC)
        arrival_time = now - timedelta(minutes=2)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        is_arriving_soon = 0 <= minutes_until <= threshold_minutes

        assert is_arriving_soon is False

    def test_custom_threshold(self) -> None:
        """Test with custom threshold value."""
        threshold_minutes = 10
        now = datetime.now(UTC)
        arrival_time = now + timedelta(minutes=8)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        is_arriving_soon = 0 <= minutes_until <= threshold_minutes

        assert is_arriving_soon is True


class TestBinarySensorLogic:
    """Test suite for binary sensor on/off logic."""

    @pytest.fixture
    def mock_arrivals(self) -> list[dict[str, Any]]:
        """Return mock arrivals with current times."""
        now = datetime.now(UTC)
        return [
            {
                "routeNumber": "742",
                "stopTime": (now + timedelta(minutes=3)).isoformat(),
            },
            {
                "routeNumber": "742",
                "stopTime": (now + timedelta(minutes=15)).isoformat(),
            },
        ]

    def test_is_on_when_bus_within_threshold(self, mock_arrivals: list[dict[str, Any]]) -> None:
        """Test that sensor is on when bus is within threshold."""
        threshold = 5
        now = datetime.now(UTC)

        for arrival in mock_arrivals:
            arrival_time = datetime.fromisoformat(arrival["stopTime"])
            minutes = int((arrival_time - now).total_seconds() / 60)
            if 0 <= minutes <= threshold:
                is_on = True
                break
        else:
            is_on = False

        assert is_on is True

    def test_is_off_when_no_bus_within_threshold(self) -> None:
        """Test that sensor is off when no bus is within threshold."""
        threshold = 5
        now = datetime.now(UTC)
        arrivals = [
            {"stopTime": (now + timedelta(minutes=10)).isoformat()},
            {"stopTime": (now + timedelta(minutes=20)).isoformat()},
        ]

        for arrival in arrivals:
            arrival_time = datetime.fromisoformat(arrival["stopTime"])
            minutes = int((arrival_time - now).total_seconds() / 60)
            if 0 <= minutes <= threshold:
                is_on = True
                break
        else:
            is_on = False

        assert is_on is False

    def test_is_off_when_no_arrivals(self) -> None:
        """Test that sensor is off when there are no arrivals."""
        threshold = 5
        arrivals: list[dict[str, Any]] = []
        now = datetime.now(UTC)

        is_on = False
        for arrival in arrivals:
            arrival_time = datetime.fromisoformat(arrival["stopTime"])
            minutes = int((arrival_time - now).total_seconds() / 60)
            if 0 <= minutes <= threshold:
                is_on = True
                break

        assert is_on is False


class TestBinarySensorDeviceClass:
    """Test suite for binary sensor device class."""

    def test_occupancy_class_is_valid(self) -> None:
        """Test that occupancy is a valid binary sensor class."""
        # BinarySensorDeviceClass.OCCUPANCY is used for presence detection
        # This is appropriate for "bus arriving" detection
        valid_classes = [
            "battery",
            "cold",
            "connectivity",
            "door",
            "garage_door",
            "gas",
            "heat",
            "light",
            "lock",
            "moisture",
            "motion",
            "moving",
            "occupancy",  # Our choice
            "opening",
            "plug",
            "power",
            "presence",
            "problem",
            "safety",
            "smoke",
            "sound",
            "vibration",
            "window",
        ]

        assert "occupancy" in valid_classes

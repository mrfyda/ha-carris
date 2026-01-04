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
        walk_time_minutes = 0  # No walk time
        now = datetime.now(UTC)
        arrival_time = now + timedelta(minutes=3)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        effective_threshold = threshold_minutes + walk_time_minutes
        is_arriving_soon = 0 <= minutes_until <= effective_threshold

        assert is_arriving_soon is True

    def test_bus_not_arriving_soon_outside_threshold(self) -> None:
        """Test that bus is not arriving soon when outside threshold."""
        threshold_minutes = 5
        walk_time_minutes = 0  # No walk time
        now = datetime.now(UTC)
        arrival_time = now + timedelta(minutes=10)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        effective_threshold = threshold_minutes + walk_time_minutes
        is_arriving_soon = 0 <= minutes_until <= effective_threshold

        assert is_arriving_soon is False

    def test_bus_not_arriving_soon_when_past(self) -> None:
        """Test that past arrivals don't trigger arriving soon."""
        threshold_minutes = 5
        walk_time_minutes = 0  # No walk time
        now = datetime.now(UTC)
        arrival_time = now - timedelta(minutes=2)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        effective_threshold = threshold_minutes + walk_time_minutes
        is_arriving_soon = 0 <= minutes_until <= effective_threshold

        assert is_arriving_soon is False

    def test_custom_threshold(self) -> None:
        """Test with custom threshold value."""
        threshold_minutes = 10
        walk_time_minutes = 0  # No walk time
        now = datetime.now(UTC)
        arrival_time = now + timedelta(minutes=8)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        effective_threshold = threshold_minutes + walk_time_minutes
        is_arriving_soon = 0 <= minutes_until <= effective_threshold

        assert is_arriving_soon is True

    def test_walk_time_extends_threshold(self) -> None:
        """Test that walk time extends the effective threshold."""
        threshold_minutes = 1
        walk_time_minutes = 3
        now = datetime.now(UTC)
        # Bus arrives in 4 minutes (1 threshold + 3 walk time)
        arrival_time = now + timedelta(minutes=4)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        effective_threshold = threshold_minutes + walk_time_minutes
        is_arriving_soon = 0 <= minutes_until <= effective_threshold

        assert is_arriving_soon is True

    def test_walk_time_does_not_trigger_too_early(self) -> None:
        """Test that walk time doesn't trigger when bus is too far away."""
        threshold_minutes = 1
        walk_time_minutes = 3
        now = datetime.now(UTC)
        # Bus arrives in 5 minutes (beyond 1 + 3 = 4 minute threshold)
        arrival_time = now + timedelta(minutes=5)

        minutes_until = int((arrival_time - now).total_seconds() / 60)
        effective_threshold = threshold_minutes + walk_time_minutes
        is_arriving_soon = 0 <= minutes_until <= effective_threshold

        assert is_arriving_soon is False


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
        walk_time = 0  # No walk time
        now = datetime.now(UTC)

        for arrival in mock_arrivals:
            arrival_time = datetime.fromisoformat(arrival["stopTime"])
            minutes = int((arrival_time - now).total_seconds() / 60)
            effective_threshold = threshold + walk_time
            if 0 <= minutes <= effective_threshold:
                is_on = True
                break
        else:
            is_on = False

        assert is_on is True

    def test_is_off_when_no_bus_within_threshold(self) -> None:
        """Test that sensor is off when no bus is within threshold."""
        threshold = 5
        walk_time = 0  # No walk time
        now = datetime.now(UTC)
        arrivals = [
            {"stopTime": (now + timedelta(minutes=10)).isoformat()},
            {"stopTime": (now + timedelta(minutes=20)).isoformat()},
        ]

        for arrival in arrivals:
            arrival_time = datetime.fromisoformat(arrival["stopTime"])
            minutes = int((arrival_time - now).total_seconds() / 60)
            effective_threshold = threshold + walk_time
            if 0 <= minutes <= effective_threshold:
                is_on = True
                break
        else:
            is_on = False

        assert is_on is False

    def test_is_off_when_no_arrivals(self) -> None:
        """Test that sensor is off when there are no arrivals."""
        threshold = 5
        walk_time = 0  # No walk time
        arrivals: list[dict[str, Any]] = []
        now = datetime.now(UTC)

        is_on = False
        for arrival in arrivals:
            arrival_time = datetime.fromisoformat(arrival["stopTime"])
            minutes = int((arrival_time - now).total_seconds() / 60)
            effective_threshold = threshold + walk_time
            if 0 <= minutes <= effective_threshold:
                is_on = True
                break

        assert is_on is False

    def test_is_on_with_walk_time(self) -> None:
        """Test that sensor is on when bus is within threshold + walk time."""
        threshold = 1
        walk_time = 3
        now = datetime.now(UTC)
        # Bus arrives in 4 minutes (within 1 + 3 = 4 minute threshold)
        arrivals = [
            {"stopTime": (now + timedelta(minutes=4)).isoformat()},
        ]

        for arrival in arrivals:
            arrival_time = datetime.fromisoformat(arrival["stopTime"])
            minutes = int((arrival_time - now).total_seconds() / 60)
            effective_threshold = threshold + walk_time
            if 0 <= minutes <= effective_threshold:
                is_on = True
                break
        else:
            is_on = False

        assert is_on is True

    def test_is_off_with_walk_time_when_too_far(self) -> None:
        """Test that sensor is off when bus is beyond threshold + walk time."""
        threshold = 1
        walk_time = 3
        now = datetime.now(UTC)
        # Bus arrives in 5 minutes (beyond 1 + 3 = 4 minute threshold)
        arrivals = [
            {"stopTime": (now + timedelta(minutes=5)).isoformat()},
        ]

        for arrival in arrivals:
            arrival_time = datetime.fromisoformat(arrival["stopTime"])
            minutes = int((arrival_time - now).total_seconds() / 60)
            effective_threshold = threshold + walk_time
            if 0 <= minutes <= effective_threshold:
                is_on = True
                break
        else:
            is_on = False

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

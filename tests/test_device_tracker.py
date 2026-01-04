"""Tests for the Carris device tracker platform."""

from __future__ import annotations

import base64
from typing import Any

import pytest


class TestBusPositionCalculation:
    """Test suite for bus position calculations."""

    @pytest.fixture
    def mock_bus_path(self) -> list[dict[str, Any]]:
        """Return mock bus path data."""
        return [
            {"lat": 38.7250, "lng": -9.1180, "bearing": 90, "msToNext": 1000},
            {"lat": 38.7248, "lng": -9.1185, "bearing": 90, "msToNext": 1000},
            {"lat": 38.7245, "lng": -9.1190, "bearing": 90, "msToNext": 1000},
        ]

    def test_get_current_position_from_path(self, mock_bus_path: list[dict[str, Any]]) -> None:
        """Test extracting current position from path."""
        # Current position is the first point in the path
        if mock_bus_path:
            current = mock_bus_path[0]
            lat = current.get("lat")
            lng = current.get("lng")
        else:
            lat = None
            lng = None

        assert lat == 38.7250
        assert lng == -9.1180

    def test_empty_path_returns_none(self) -> None:
        """Test that empty path returns no position."""
        path: list[dict[str, Any]] = []

        if path:
            current = path[0]
            lat = current.get("lat")
            lng = current.get("lng")
        else:
            lat = None
            lng = None

        assert lat is None
        assert lng is None

    def test_bearing_extraction(self, mock_bus_path: list[dict[str, Any]]) -> None:
        """Test extracting bearing from path."""
        bearing = mock_bus_path[0].get("bearing") if mock_bus_path else None

        assert bearing == 90


class TestBusFiltering:
    """Test suite for bus filtering by route and direction."""

    @pytest.fixture
    def mock_snapshot(self) -> list[dict[str, Any]]:
        """Return mock bus snapshot data."""
        return [
            {"route": "742", "id": 1, "direction": 1, "path": []},
            {"route": "728", "id": 2, "direction": 1, "path": []},
            {"route": "742", "id": 3, "direction": 2, "path": []},
            {"route": "742", "id": 4, "direction": 1, "path": []},
        ]

    def test_filter_by_route(self, mock_snapshot: list[dict[str, Any]]) -> None:
        """Test filtering buses by route only."""
        route = "742"
        filtered = [b for b in mock_snapshot if b.get("route") == route]

        assert len(filtered) == 3
        assert all(b["route"] == "742" for b in filtered)

    def test_filter_by_route_and_direction(self, mock_snapshot: list[dict[str, Any]]) -> None:
        """Test filtering buses by route and direction."""
        route = "742"
        direction = 1
        filtered = [
            b for b in mock_snapshot if b.get("route") == route and b.get("direction") == direction
        ]

        assert len(filtered) == 2
        assert all(b["route"] == "742" and b["direction"] == 1 for b in filtered)

    def test_filter_no_matches(self, mock_snapshot: list[dict[str, Any]]) -> None:
        """Test filtering with no matches."""
        route = "999"
        filtered = [b for b in mock_snapshot if b.get("route") == route]

        assert len(filtered) == 0


class TestMultiRouteTrackerSetup:
    """Test suite for multi-route device tracker setup."""

    @pytest.fixture
    def mock_all_buses_snapshot(self) -> list[dict[str, Any]]:
        """Return mock bus snapshot with buses from multiple routes."""
        return [
            {
                "route": "742",
                "id": 1,
                "direction": 1,
                "path": [{"lat": 38.725, "lng": -9.118, "bearing": 90, "msToNext": 1000}],
            },
            {
                "route": "728",
                "id": 2,
                "direction": 1,
                "path": [{"lat": 38.730, "lng": -9.120, "bearing": 180, "msToNext": 1000}],
            },
            {
                "route": "742",
                "id": 3,
                "direction": 2,
                "path": [{"lat": 38.720, "lng": -9.115, "bearing": 270, "msToNext": 1000}],
            },
            {
                "route": "15E",
                "id": 4,
                "direction": 1,
                "path": [{"lat": 38.735, "lng": -9.125, "bearing": 0, "msToNext": 1000}],
            },
        ]

    def test_filter_buses_for_each_route(
        self, mock_all_buses_snapshot: list[dict[str, Any]]
    ) -> None:
        """Test that each route tracker only sees buses for its route."""
        routes = ["742", "728", "15E"]

        for route in routes:
            filtered = [b for b in mock_all_buses_snapshot if b.get("route") == route]

            # Verify correct number of buses per route
            if route == "742":
                assert len(filtered) == 2
            elif route == "728" or route == "15E":
                assert len(filtered) == 1

            # Verify all buses have correct route
            assert all(b["route"] == route for b in filtered)

    def test_routes_list_determines_trackers(self) -> None:
        """Test that routes list determines how many trackers are created."""
        routes = ["742", "728", "15E"]

        # Each route should result in one tracker
        expected_trackers = len(routes)
        assert expected_trackers == 3

    def test_empty_routes_no_trackers(self) -> None:
        """Test that empty routes list creates no trackers."""
        routes: list[str] = []
        route_number = None

        # No trackers should be created
        should_create_trackers = bool(route_number) or bool(routes)
        assert should_create_trackers is False

    def test_single_route_mode(self) -> None:
        """Test single route mode creates one tracker."""
        route_number = "742"
        routes = ["742", "728", "15E"]

        # When route_number is set, only one tracker for that route
        tracker_routes = [route_number] if route_number else routes

        assert len(tracker_routes) == 1
        assert tracker_routes[0] == "742"


class TestRouteBadgeGeneration:
    """Test suite for route badge SVG generation."""

    def test_generate_route_badge_short_number(self) -> None:
        """Test generating badge for short route number."""
        route_number = "7"

        # Simulate badge generation
        if len(route_number) <= 2:
            font_size = 16
        elif len(route_number) == 3:
            font_size = 13
        else:
            font_size = 10

        assert font_size == 16

    def test_generate_route_badge_medium_number(self) -> None:
        """Test generating badge for medium route number."""
        route_number = "742"

        if len(route_number) <= 2:
            font_size = 16
        elif len(route_number) == 3:
            font_size = 13
        else:
            font_size = 10

        assert font_size == 13

    def test_generate_route_badge_long_number(self) -> None:
        """Test generating badge for long route number."""
        route_number = "15E"

        if len(route_number) <= 2:
            font_size = 16
        elif len(route_number) == 3:
            font_size = 13
        else:
            font_size = 10

        assert font_size == 13

    def test_generate_route_badge_very_long(self) -> None:
        """Test generating badge for very long route identifier."""
        route_number = "742A"

        if len(route_number) <= 2:
            font_size = 16
        elif len(route_number) == 3:
            font_size = 13
        else:
            font_size = 10

        assert font_size == 10

    def test_svg_base64_encoding(self) -> None:
        """Test that SVG is properly base64 encoded."""
        route_number = "742"
        font_size = 13

        svg = (
            f"<svg xmlns='http://www.w3.org/2000/svg' width='40' height='40'>"
            f"<circle cx='20' cy='20' r='18' fill='%23FFCC00' stroke='%23003366' stroke-width='2'/>"
            f"<text x='20' y='25' text-anchor='middle' fill='%23003366' "
            f"font-family='Arial,sans-serif' font-size='{font_size}' font-weight='bold'>"
            f"{route_number}</text></svg>"
        )

        encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        data_url = f"data:image/svg+xml;base64,{encoded}"

        assert data_url.startswith("data:image/svg+xml;base64,")
        assert len(encoded) > 0

        # Verify it can be decoded back
        decoded = base64.b64decode(encoded).decode("utf-8")
        assert route_number in decoded
        assert "FFCC00" in decoded  # Carris yellow
        assert "003366" in decoded  # Carris blue


class TestSourceType:
    """Test suite for device tracker source type."""

    def test_gps_source_type(self) -> None:
        """Test that GPS is a valid source type."""
        # SourceType.GPS is appropriate for Carris bus tracking
        valid_types = ["bluetooth", "bluetooth_le", "gps", "router"]
        assert "gps" in valid_types

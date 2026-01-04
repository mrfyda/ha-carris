"""Fixtures for Carris integration tests."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import MagicMock

import pytest

# Mock homeassistant modules before any test imports
_HA_MOCKS = [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.exceptions",
    "homeassistant.helpers",
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.helpers.device_registry",
    "homeassistant.helpers.entity_platform",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.binary_sensor",
    "homeassistant.components.device_tracker",
    "homeassistant.components.device_tracker.config_entry",
    "homeassistant.components.diagnostics",
    "homeassistant.data_entry_flow",
    "voluptuous",
]

for mod in _HA_MOCKS:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()


@pytest.fixture
def mock_stop_info() -> dict[str, Any]:
    """Return mock stop info."""
    return {
        "id": 9804,
        "name": "R. D. Fuas Roupinho",
        "location": {"lat": 38.7244087, "lng": -9.1173888},
        "routes": [
            {"routeNumber": "742", "color": "#8c8c99"},
            {"routeNumber": "728", "color": "#ff0000"},
        ],
    }


@pytest.fixture
def mock_next_buses() -> list[dict[str, Any]]:
    """Return mock next buses data."""
    return [
        {
            "routeNumber": "742",
            "stopId": 9804,
            "stopTime": "2026-01-04T14:08:32+00:00",
            "destination": "Pólo Univ. Ajuda",
        },
        {
            "routeNumber": "742",
            "stopId": 9804,
            "stopTime": "2026-01-04T14:23:32+00:00",
            "destination": "Pólo Univ. Ajuda",
        },
        {
            "routeNumber": "728",
            "stopId": 9804,
            "stopTime": "2026-01-04T14:15:00+00:00",
            "destination": "Restelo",
        },
    ]


@pytest.fixture
def mock_bus_snapshot() -> list[dict[str, Any]]:
    """Return mock bus snapshot data."""
    return [
        {
            "route": "742",
            "plate": "4Z758",
            "type": 1,
            "zone": 1,
            "id": 12345,
            "state": 1,
            "path": [
                {"lat": 38.7250, "lng": -9.1180, "bearing": 90, "msToNext": 1000},
                {"lat": 38.7248, "lng": -9.1185, "bearing": 90, "msToNext": 1000},
            ],
            "version": 1,
            "direction": 1,
            "variantNumber": 1,
        },
        {
            "route": "742",
            "plate": "5Z123",
            "type": 1,
            "zone": 1,
            "id": 12346,
            "state": 1,
            "path": [
                {"lat": 38.7300, "lng": -9.1200, "bearing": 180, "msToNext": 1000},
            ],
            "version": 1,
            "direction": 1,
            "variantNumber": 1,
        },
    ]


@pytest.fixture
def mock_token_response() -> dict[str, Any]:
    """Return mock token response."""
    return {
        "access_token": "test_access_token_12345",
        "token_type": "bearer",
        "expires_in": 86399,
    }


@pytest.fixture
def mock_all_stops() -> list[dict[str, Any]]:
    """Return mock all stops data."""
    return [
        {
            "id": 9803,
            "name": "R. D. Fuas Roupinho",
            "location": {"lat": 38.7244087, "lng": -9.1173888},
            "routes": [{"routeNumber": "742", "color": "#8c8c99"}],
        },
        {
            "id": 9804,
            "name": "R. D. Fuas Roupinho",
            "location": {"lat": 38.7244087, "lng": -9.1173888},
            "routes": [{"routeNumber": "742", "color": "#8c8c99"}],
        },
        {
            "id": 1234,
            "name": "Praça do Comércio",
            "location": {"lat": 38.7075, "lng": -9.1364},
            "routes": [
                {"routeNumber": "15E", "color": "#ff0000"},
                {"routeNumber": "25E", "color": "#00ff00"},
            ],
        },
    ]

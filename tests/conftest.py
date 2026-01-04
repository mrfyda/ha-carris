"""Fixtures for Carris integration tests."""
from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.carris.const import (
    CONF_ROUTE_NUMBER,
    CONF_STOP_ID,
    CONF_STOP_LAT,
    CONF_STOP_LNG,
    CONF_STOP_NAME,
    DOMAIN,
)


@pytest.fixture
def mock_config_entry() -> ConfigEntry:
    """Create a mock config entry."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Carris 742 - R. D. Fuas Roupinho",
        data={
            CONF_STOP_ID: 9804,
            CONF_STOP_NAME: "R. D. Fuas Roupinho",
            CONF_ROUTE_NUMBER: "742",
            CONF_STOP_LAT: 38.7244087,
            CONF_STOP_LNG: -9.1173888,
        },
        source="user",
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_config_entry_all_routes() -> ConfigEntry:
    """Create a mock config entry for all routes."""
    return ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Carris - R. D. Fuas Roupinho",
        data={
            CONF_STOP_ID: 9804,
            CONF_STOP_NAME: "R. D. Fuas Roupinho",
            CONF_STOP_LAT: 38.7244087,
            CONF_STOP_LNG: -9.1173888,
        },
        source="user",
        entry_id="test_entry_all_routes",
    )


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


@pytest.fixture
def mock_aiohttp_session() -> Generator[MagicMock, None, None]:
    """Create a mock aiohttp session."""
    with patch("aiohttp.ClientSession") as mock_session:
        yield mock_session


@pytest.fixture
def mock_carris_api_client() -> Generator[AsyncMock, None, None]:
    """Create a mock Carris API client."""
    with patch(
        "custom_components.carris.api.CarrisApiClient", autospec=True
    ) as mock_client:
        client_instance = mock_client.return_value
        client_instance.refresh_token = AsyncMock(return_value="test_token")
        client_instance.get_next_buses = AsyncMock(return_value=[])
        client_instance.get_all_stops = AsyncMock(return_value=[])
        client_instance.get_bus_snapshot = AsyncMock(return_value=[])
        client_instance.get_buses_for_route = AsyncMock(return_value=[])
        client_instance.get_direction_for_stop = AsyncMock(return_value=1)
        client_instance.validate_stop = AsyncMock(return_value=None)
        client_instance.has_token = True
        yield client_instance


"""Tests for the Carris API client."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.carris.api import CarrisApiClient


class TestCarrisApiClient:
    """Test suite for CarrisApiClient."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock aiohttp session."""
        return MagicMock(spec=aiohttp.ClientSession)

    @pytest.fixture
    def api_client(self, mock_session: MagicMock) -> CarrisApiClient:
        """Create a CarrisApiClient instance."""
        return CarrisApiClient(mock_session)

    async def test_has_token_false_initially(
        self, api_client: CarrisApiClient
    ) -> None:
        """Test that has_token is False initially."""
        assert api_client.has_token is False

    async def test_refresh_token_success(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Test successful token refresh."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value=mock_token_response)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=mock_response)

        token = await api_client.refresh_token()

        assert token == "test_access_token_12345"
        assert api_client.has_token is True

    async def test_get_next_buses_success(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_next_buses: list[dict[str, Any]],
    ) -> None:
        """Test successful get_next_buses call."""
        # Setup token response
        token_response = AsyncMock()
        token_response.status = 200
        token_response.raise_for_status = MagicMock()
        token_response.json = AsyncMock(return_value=mock_token_response)
        token_response.__aenter__ = AsyncMock(return_value=token_response)
        token_response.__aexit__ = AsyncMock(return_value=None)

        # Setup buses response
        buses_response = AsyncMock()
        buses_response.status = 200
        buses_response.raise_for_status = MagicMock()
        buses_response.json = AsyncMock(return_value=mock_next_buses)
        buses_response.__aenter__ = AsyncMock(return_value=buses_response)
        buses_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=buses_response)

        buses = await api_client.get_next_buses(9804)

        assert len(buses) == 3
        assert buses[0]["routeNumber"] == "742"
        assert buses[0]["destination"] == "Pólo Univ. Ajuda"

    async def test_get_all_stops_success(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test successful get_all_stops call."""
        # Setup token response
        token_response = AsyncMock()
        token_response.status = 200
        token_response.raise_for_status = MagicMock()
        token_response.json = AsyncMock(return_value=mock_token_response)
        token_response.__aenter__ = AsyncMock(return_value=token_response)
        token_response.__aexit__ = AsyncMock(return_value=None)

        # Setup stops response
        stops_response = AsyncMock()
        stops_response.status = 200
        stops_response.raise_for_status = MagicMock()
        stops_response.json = AsyncMock(return_value=mock_all_stops)
        stops_response.__aenter__ = AsyncMock(return_value=stops_response)
        stops_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        stops = await api_client.get_all_stops()

        assert len(stops) == 3
        assert stops[0]["id"] == 9803
        assert stops[2]["name"] == "Praça do Comércio"

    async def test_get_bus_snapshot_success(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_bus_snapshot: list[dict[str, Any]],
    ) -> None:
        """Test successful get_bus_snapshot call."""
        # Setup token response
        token_response = AsyncMock()
        token_response.status = 200
        token_response.raise_for_status = MagicMock()
        token_response.json = AsyncMock(return_value=mock_token_response)
        token_response.__aenter__ = AsyncMock(return_value=token_response)
        token_response.__aexit__ = AsyncMock(return_value=None)

        # Setup snapshot response
        snapshot_response = AsyncMock()
        snapshot_response.status = 200
        snapshot_response.raise_for_status = MagicMock()
        snapshot_response.json = AsyncMock(return_value=mock_bus_snapshot)
        snapshot_response.__aenter__ = AsyncMock(return_value=snapshot_response)
        snapshot_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=snapshot_response)

        snapshot = await api_client.get_bus_snapshot()

        assert len(snapshot) == 2
        assert snapshot[0]["route"] == "742"
        assert snapshot[0]["plate"] == "4Z758"

    async def test_get_buses_for_route_filters_correctly(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Test that get_buses_for_route filters by route number."""
        # Create mixed snapshot with different routes
        mixed_snapshot = [
            {"route": "742", "id": 1, "path": []},
            {"route": "728", "id": 2, "path": []},
            {"route": "742", "id": 3, "path": []},
        ]

        # Setup token response
        token_response = AsyncMock()
        token_response.status = 200
        token_response.raise_for_status = MagicMock()
        token_response.json = AsyncMock(return_value=mock_token_response)
        token_response.__aenter__ = AsyncMock(return_value=token_response)
        token_response.__aexit__ = AsyncMock(return_value=None)

        # Setup snapshot response
        snapshot_response = AsyncMock()
        snapshot_response.status = 200
        snapshot_response.raise_for_status = MagicMock()
        snapshot_response.json = AsyncMock(return_value=mixed_snapshot)
        snapshot_response.__aenter__ = AsyncMock(return_value=snapshot_response)
        snapshot_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=snapshot_response)

        buses = await api_client.get_buses_for_route("742")

        assert len(buses) == 2
        assert all(bus["route"] == "742" for bus in buses)

    async def test_validate_stop_found(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test validate_stop returns stop info when found."""
        # Setup token response
        token_response = AsyncMock()
        token_response.status = 200
        token_response.raise_for_status = MagicMock()
        token_response.json = AsyncMock(return_value=mock_token_response)
        token_response.__aenter__ = AsyncMock(return_value=token_response)
        token_response.__aexit__ = AsyncMock(return_value=None)

        # Setup stops response
        stops_response = AsyncMock()
        stops_response.status = 200
        stops_response.raise_for_status = MagicMock()
        stops_response.json = AsyncMock(return_value=mock_all_stops)
        stops_response.__aenter__ = AsyncMock(return_value=stops_response)
        stops_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        stop = await api_client.validate_stop(9804)

        assert stop is not None
        assert stop["id"] == 9804

    async def test_validate_stop_not_found(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test validate_stop returns None when not found."""
        # Setup token response
        token_response = AsyncMock()
        token_response.status = 200
        token_response.raise_for_status = MagicMock()
        token_response.json = AsyncMock(return_value=mock_token_response)
        token_response.__aenter__ = AsyncMock(return_value=token_response)
        token_response.__aexit__ = AsyncMock(return_value=None)

        # Setup stops response
        stops_response = AsyncMock()
        stops_response.status = 200
        stops_response.raise_for_status = MagicMock()
        stops_response.json = AsyncMock(return_value=mock_all_stops)
        stops_response.__aenter__ = AsyncMock(return_value=stops_response)
        stops_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        stop = await api_client.validate_stop(99999)

        assert stop is None

    async def test_token_refresh_on_401(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_next_buses: list[dict[str, Any]],
    ) -> None:
        """Test that token is refreshed on 401 response."""
        # Setup token response
        token_response = AsyncMock()
        token_response.status = 200
        token_response.raise_for_status = MagicMock()
        token_response.json = AsyncMock(return_value=mock_token_response)
        token_response.__aenter__ = AsyncMock(return_value=token_response)
        token_response.__aexit__ = AsyncMock(return_value=None)

        # First call returns 401, second returns success
        first_response = AsyncMock()
        first_response.status = 401
        first_response.__aenter__ = AsyncMock(return_value=first_response)
        first_response.__aexit__ = AsyncMock(return_value=None)

        retry_response = AsyncMock()
        retry_response.status = 200
        retry_response.raise_for_status = MagicMock()
        retry_response.json = AsyncMock(return_value=mock_next_buses)
        retry_response.__aenter__ = AsyncMock(return_value=retry_response)
        retry_response.__aexit__ = AsyncMock(return_value=None)

        mock_session.post = MagicMock(return_value=token_response)
        # Return 401 first, then success on retry
        mock_session.get = MagicMock(side_effect=[first_response, retry_response])

        # First get a token
        await api_client.refresh_token()

        buses = await api_client.get_next_buses(9804)

        assert len(buses) == 3
        # Verify post was called twice (initial token + refresh)
        assert mock_session.post.call_count == 2


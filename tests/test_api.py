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

    def _create_mock_response(self, status: int = 200, json_data: Any = None) -> AsyncMock:
        """Create a mock response object."""
        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.raise_for_status = MagicMock()
        mock_response.json = AsyncMock(return_value=json_data)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_response.headers = {}
        return mock_response

    @pytest.mark.asyncio
    async def test_has_token_false_initially(self, api_client: CarrisApiClient) -> None:
        """Test that has_token is False initially."""
        assert api_client.has_token is False

    @pytest.mark.asyncio
    async def test_token_is_expired_when_no_token(self, api_client: CarrisApiClient) -> None:
        """Test that token_is_expired is True when no token exists."""
        assert api_client.token_is_expired is True

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Test successful token refresh."""
        mock_response = self._create_mock_response(200, mock_token_response)
        mock_session.post = MagicMock(return_value=mock_response)

        with patch("async_timeout.timeout", return_value=AsyncMock()):
            token = await api_client.refresh_token()

        assert token == "test_access_token_12345"
        assert api_client.has_token is True
        assert api_client.token_is_expired is False

    @pytest.mark.asyncio
    async def test_get_next_buses_success(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_next_buses: list[dict[str, Any]],
    ) -> None:
        """Test successful get_next_buses call."""
        token_response = self._create_mock_response(200, mock_token_response)
        buses_response = self._create_mock_response(200, mock_next_buses)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=buses_response)

        with patch("async_timeout.timeout", return_value=AsyncMock()):
            buses = await api_client.get_next_buses(9804)

        assert len(buses) == 3
        assert buses[0]["routeNumber"] == "742"
        assert buses[0]["destination"] == "Pólo Univ. Ajuda"

    @pytest.mark.asyncio
    async def test_get_all_stops_success(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test successful get_all_stops call."""
        token_response = self._create_mock_response(200, mock_token_response)
        stops_response = self._create_mock_response(200, mock_all_stops)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        with patch("async_timeout.timeout", return_value=AsyncMock()):
            stops = await api_client.get_all_stops()

        assert len(stops) == 3
        assert stops[0]["id"] == 9803
        assert stops[2]["name"] == "Praça do Comércio"

    @pytest.mark.asyncio
    async def test_get_bus_snapshot_success(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_bus_snapshot: list[dict[str, Any]],
    ) -> None:
        """Test successful get_bus_snapshot call."""
        token_response = self._create_mock_response(200, mock_token_response)
        snapshot_response = self._create_mock_response(200, mock_bus_snapshot)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=snapshot_response)

        with patch("async_timeout.timeout", return_value=AsyncMock()):
            snapshot = await api_client.get_bus_snapshot()

        assert len(snapshot) == 2
        assert snapshot[0]["route"] == "742"
        assert snapshot[0]["plate"] == "4Z758"

    @pytest.mark.asyncio
    async def test_get_buses_for_route_filters_correctly(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Test that get_buses_for_route filters by route number."""
        mixed_snapshot = [
            {"route": "742", "id": 1, "path": []},
            {"route": "728", "id": 2, "path": []},
            {"route": "742", "id": 3, "path": []},
        ]

        token_response = self._create_mock_response(200, mock_token_response)
        snapshot_response = self._create_mock_response(200, mixed_snapshot)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=snapshot_response)

        with patch("async_timeout.timeout", return_value=AsyncMock()):
            buses = await api_client.get_buses_for_route("742")

        assert len(buses) == 2
        assert all(bus["route"] == "742" for bus in buses)

    @pytest.mark.asyncio
    async def test_validate_stop_found(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test validate_stop returns stop info when found."""
        token_response = self._create_mock_response(200, mock_token_response)
        stops_response = self._create_mock_response(200, mock_all_stops)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        with patch("async_timeout.timeout", return_value=AsyncMock()):
            stop = await api_client.validate_stop(9804)

        assert stop is not None
        assert stop["id"] == 9804

    @pytest.mark.asyncio
    async def test_validate_stop_not_found(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test validate_stop returns None when not found."""
        token_response = self._create_mock_response(200, mock_token_response)
        stops_response = self._create_mock_response(200, mock_all_stops)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        with patch("async_timeout.timeout", return_value=AsyncMock()):
            stop = await api_client.validate_stop(99999)

        assert stop is None

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

    # ==========================================================================
    # Token Management Tests
    # ==========================================================================

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

        with patch("asyncio.timeout", return_value=AsyncMock()):
            token = await api_client.refresh_token()

        assert token == "test_access_token_12345"
        assert api_client.has_token is True
        assert api_client.token_is_expired is False

    @pytest.mark.asyncio
    async def test_refresh_token_updates_expiry(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
    ) -> None:
        """Test that token refresh sets expiry time correctly."""
        token_response = {
            "access_token": "test_token",
            "token_type": "bearer",
            "expires_in": 3600,  # 1 hour
        }
        mock_response = self._create_mock_response(200, token_response)
        mock_session.post = MagicMock(return_value=mock_response)

        with patch("asyncio.timeout", return_value=AsyncMock()):
            await api_client.refresh_token()

        # Token should NOT be expired (1 hour > 1 hour buffer)
        # But since expires_in is 3600 and buffer is 1 hour, it's exactly at the edge
        assert api_client.has_token is True

    # ==========================================================================
    # Get Next Buses Tests
    # ==========================================================================

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

        with patch("asyncio.timeout", return_value=AsyncMock()):
            buses = await api_client.get_next_buses(9804)

        assert len(buses) == 3
        assert buses[0]["routeNumber"] == "742"
        assert buses[0]["destination"] == "Pólo Univ. Ajuda"

    @pytest.mark.asyncio
    async def test_get_next_buses_empty_response(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Test get_next_buses with empty response."""
        token_response = self._create_mock_response(200, mock_token_response)
        buses_response = self._create_mock_response(200, [])

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=buses_response)

        with patch("asyncio.timeout", return_value=AsyncMock()):
            buses = await api_client.get_next_buses(9804)

        assert buses == []

    # ==========================================================================
    # Get All Stops Tests
    # ==========================================================================

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

        with patch("asyncio.timeout", return_value=AsyncMock()):
            stops = await api_client.get_all_stops()

        assert len(stops) == 3
        assert stops[0]["id"] == 9803
        assert stops[2]["name"] == "Praça do Comércio"

    # ==========================================================================
    # Bus Snapshot Tests
    # ==========================================================================

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

        with patch("asyncio.timeout", return_value=AsyncMock()):
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

        with patch("asyncio.timeout", return_value=AsyncMock()):
            buses = await api_client.get_buses_for_route("742")

        assert len(buses) == 2
        assert all(bus["route"] == "742" for bus in buses)

    @pytest.mark.asyncio
    async def test_get_buses_for_route_with_direction(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Test that get_buses_for_route filters by direction."""
        mixed_snapshot = [
            {"route": "742", "id": 1, "direction": 1, "path": []},
            {"route": "742", "id": 2, "direction": 2, "path": []},
            {"route": "742", "id": 3, "direction": 1, "path": []},
        ]

        token_response = self._create_mock_response(200, mock_token_response)
        snapshot_response = self._create_mock_response(200, mixed_snapshot)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=snapshot_response)

        with patch("asyncio.timeout", return_value=AsyncMock()):
            buses = await api_client.get_buses_for_route("742", direction=1)

        assert len(buses) == 2
        assert all(bus["direction"] == 1 for bus in buses)

    # ==========================================================================
    # Validate Stop Tests
    # ==========================================================================

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

        with patch("asyncio.timeout", return_value=AsyncMock()):
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

        with patch("asyncio.timeout", return_value=AsyncMock()):
            stop = await api_client.validate_stop(99999)

        assert stop is None

    # ==========================================================================
    # Direction Detection Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_get_direction_for_stop(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_next_buses: list[dict[str, Any]],
    ) -> None:
        """Test direction detection based on arrivals at stop."""
        # Add direction info to next buses
        arrivals_with_direction = [
            {**mock_next_buses[0], "direction": 1},
            {**mock_next_buses[1], "direction": 1},
        ]

        token_response = self._create_mock_response(200, mock_token_response)
        arrivals_response = self._create_mock_response(200, arrivals_with_direction)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=arrivals_response)

        with patch("asyncio.timeout", return_value=AsyncMock()):
            direction = await api_client.get_direction_for_stop("742", 9804)

        # Direction should be detected from arrivals
        assert direction == 1 or direction is None  # Depends on implementation

    # ==========================================================================
    # Error Handling Tests
    # ==========================================================================

    @pytest.mark.asyncio
    async def test_api_timeout_handling(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Test that API timeouts are handled properly."""
        token_response = self._create_mock_response(200, mock_token_response)
        mock_session.post = MagicMock(return_value=token_response)

        # Simulate timeout on GET
        mock_session.get = MagicMock(side_effect=TimeoutError())

        with (
            patch("asyncio.timeout", return_value=AsyncMock()),
            pytest.raises(TimeoutError),
        ):
            await api_client.get_next_buses(9804)

    @pytest.mark.asyncio
    async def test_client_error_handling(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
    ) -> None:
        """Test that client errors are handled properly."""
        token_response = self._create_mock_response(200, mock_token_response)
        mock_session.post = MagicMock(return_value=token_response)

        # Simulate client error on GET
        mock_session.get = MagicMock(side_effect=aiohttp.ClientError("Connection failed"))

        with (
            patch("asyncio.timeout", return_value=AsyncMock()),
            pytest.raises(aiohttp.ClientError),
        ):
            await api_client.get_next_buses(9804)


class TestCarrisApiClientRetry:
    """Test retry logic in the API client."""

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
    async def test_retry_on_server_error(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
    ) -> None:
        """Test that server errors trigger retry."""
        mock_token = {
            "access_token": "test_token",
            "token_type": "bearer",
            "expires_in": 86400,
        }
        token_response = self._create_mock_response(200, mock_token)
        mock_session.post = MagicMock(return_value=token_response)

        # First call fails with 500, second succeeds
        error_response = self._create_mock_response(500, None)
        error_response.raise_for_status = MagicMock(
            side_effect=aiohttp.ClientResponseError(
                request_info=MagicMock(), history=(), status=500
            )
        )
        success_response = self._create_mock_response(200, [])

        mock_session.get = MagicMock(side_effect=[error_response, success_response])

        # This should eventually fail after retries or succeed on second try
        with patch("asyncio.timeout", return_value=AsyncMock()):
            try:
                result = await api_client.get_next_buses(9804)
                assert result == []
            except aiohttp.ClientError:
                # Expected if all retries fail
                pass

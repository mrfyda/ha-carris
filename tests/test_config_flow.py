"""Tests for the Carris config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.carris.api import CarrisApiClient


class TestValidateStop:
    """Test suite for stop validation."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock aiohttp session."""
        import aiohttp

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
    async def test_validate_stop_returns_stop_info(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test that validate_stop returns stop info for valid stop."""
        token_response = self._create_mock_response(200, mock_token_response)
        stops_response = self._create_mock_response(200, mock_all_stops)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        with patch("asyncio.timeout", return_value=AsyncMock()):
            stop = await api_client.validate_stop(9804)

        assert stop is not None
        assert stop["id"] == 9804
        assert "name" in stop
        assert "location" in stop

    @pytest.mark.asyncio
    async def test_validate_stop_returns_none_for_invalid(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test that validate_stop returns None for invalid stop."""
        token_response = self._create_mock_response(200, mock_token_response)
        stops_response = self._create_mock_response(200, mock_all_stops)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        with patch("asyncio.timeout", return_value=AsyncMock()):
            stop = await api_client.validate_stop(99999)

        assert stop is None


class TestSearchStops:
    """Test suite for stop search functionality."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock aiohttp session."""
        import aiohttp

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
    async def test_get_all_stops_for_search(
        self,
        api_client: CarrisApiClient,
        mock_session: MagicMock,
        mock_token_response: dict[str, Any],
        mock_all_stops: list[dict[str, Any]],
    ) -> None:
        """Test that get_all_stops can be used for search."""
        token_response = self._create_mock_response(200, mock_token_response)
        stops_response = self._create_mock_response(200, mock_all_stops)

        mock_session.post = MagicMock(return_value=token_response)
        mock_session.get = MagicMock(return_value=stops_response)

        with patch("asyncio.timeout", return_value=AsyncMock()):
            stops = await api_client.get_all_stops()

        # Filter by name locally (simulating search behavior)
        query = "Fuas"
        matching_stops = [s for s in stops if query.lower() in s.get("name", "").lower()]

        assert len(matching_stops) == 2
        assert all("Fuas" in s["name"] for s in matching_stops)


class TestConfigFlowConstants:
    """Test suite for config flow constants."""

    def test_error_constants_defined(self) -> None:
        """Test that error constants are defined."""
        from custom_components.carris.const import (
            ERROR_CONNECTION,
            ERROR_STOP_NOT_FOUND,
            ERROR_UNKNOWN,
        )

        assert ERROR_STOP_NOT_FOUND is not None
        assert ERROR_UNKNOWN is not None
        assert ERROR_CONNECTION is not None

    def test_config_constants_defined(self) -> None:
        """Test that config constants are defined."""
        from custom_components.carris.const import (
            CONF_ARRIVAL_THRESHOLD,
            CONF_ROUTE_NUMBER,
            CONF_SCAN_INTERVAL,
            CONF_STOP_ID,
            CONF_STOP_LAT,
            CONF_STOP_LNG,
            CONF_STOP_NAME,
        )

        assert CONF_STOP_ID is not None
        assert CONF_STOP_NAME is not None
        assert CONF_ROUTE_NUMBER is not None
        assert CONF_STOP_LAT is not None
        assert CONF_STOP_LNG is not None
        assert CONF_SCAN_INTERVAL is not None
        assert CONF_ARRIVAL_THRESHOLD is not None

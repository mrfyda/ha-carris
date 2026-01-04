"""Tests for the Carris integration initialization."""

from __future__ import annotations

import pytest

from custom_components.carris.const import (
    ATTRIBUTION,
    CONF_ARRIVAL_THRESHOLD,
    CONF_ROUTE_NUMBER,
    CONF_SCAN_INTERVAL,
    CONF_STOP_ID,
    CONF_STOP_LAT,
    CONF_STOP_LNG,
    CONF_STOP_NAME,
    DEFAULT_API_TIMEOUT,
    DEFAULT_ARRIVAL_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    MODEL_BUS_STOP,
)


class TestCarrisConstants:
    """Test suite for Carris constants."""

    def test_domain_defined(self) -> None:
        """Test that domain is properly defined."""
        assert DOMAIN == "carris"

    def test_required_config_keys_defined(self) -> None:
        """Test that all required config keys are defined."""
        assert CONF_STOP_ID == "stop_id"
        assert CONF_STOP_NAME == "stop_name"
        assert CONF_ROUTE_NUMBER == "route_number"
        assert CONF_STOP_LAT == "stop_lat"
        assert CONF_STOP_LNG == "stop_lng"
        assert CONF_SCAN_INTERVAL == "scan_interval"
        assert CONF_ARRIVAL_THRESHOLD == "arrival_threshold"

    def test_defaults_are_reasonable(self) -> None:
        """Test that default values are reasonable."""
        # Scan interval should be between 30 seconds and 5 minutes
        assert 30 <= DEFAULT_SCAN_INTERVAL <= 300
        # Arrival threshold should be between 1 and 30 minutes
        assert 1 <= DEFAULT_ARRIVAL_THRESHOLD <= 30
        # API timeout should be between 5 and 60 seconds
        assert 5 <= DEFAULT_API_TIMEOUT <= 60

    def test_manufacturer_and_model_defined(self) -> None:
        """Test that manufacturer and model are defined."""
        assert MANUFACTURER == "Carris"
        assert MODEL_BUS_STOP is not None
        assert len(MODEL_BUS_STOP) > 0

    def test_attribution_defined(self) -> None:
        """Test that attribution is defined."""
        assert ATTRIBUTION is not None
        assert "Carris" in ATTRIBUTION


class TestCarrisApiImports:
    """Test suite for API imports."""

    def test_api_client_importable(self) -> None:
        """Test that API client can be imported."""
        from custom_components.carris.api import CarrisApiClient

        assert CarrisApiClient is not None

    def test_api_types_importable(self) -> None:
        """Test that API types can be imported."""
        from custom_components.carris.api import (
            BusArrivalResponse,
            BusPathPoint,
            BusSnapshotItem,
            StopInfo,
        )

        assert BusArrivalResponse is not None
        assert BusPathPoint is not None
        assert BusSnapshotItem is not None
        assert StopInfo is not None


class TestCarrisModuleStructure:
    """Test suite for module structure."""

    def test_const_module_importable(self) -> None:
        """Test that const module can be imported."""
        from custom_components.carris import const

        assert const is not None

    def test_api_module_importable(self) -> None:
        """Test that api module can be imported."""
        from custom_components.carris import api

        assert api is not None

    @pytest.mark.asyncio
    async def test_api_client_instantiation(self) -> None:
        """Test that API client can be instantiated."""
        from unittest.mock import MagicMock

        import aiohttp

        from custom_components.carris.api import CarrisApiClient

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        client = CarrisApiClient(mock_session)

        assert client is not None
        assert client.has_token is False
        assert client.token_is_expired is True

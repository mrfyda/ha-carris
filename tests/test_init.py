"""Tests for the Carris integration initialization."""

from __future__ import annotations

import pytest

from custom_components.carris.const import (
    CONF_ROUTE_NUMBER,
    CONF_STOP_ID,
    CONF_STOP_LAT,
    CONF_STOP_LNG,
    CONF_STOP_NAME,
    DEFAULT_ARRIVAL_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class TestCarrisIntegration:
    """Test suite for Carris integration setup."""

    @pytest.mark.asyncio
    async def test_constants_defined(self) -> None:
        """Test that all required constants are defined."""
        assert DOMAIN == "carris"
        assert CONF_STOP_ID is not None
        assert CONF_STOP_NAME is not None
        assert CONF_ROUTE_NUMBER is not None
        assert CONF_STOP_LAT is not None
        assert CONF_STOP_LNG is not None
        assert DEFAULT_SCAN_INTERVAL > 0
        assert DEFAULT_ARRIVAL_THRESHOLD > 0

    @pytest.mark.asyncio
    async def test_api_client_imports(self) -> None:
        """Test that API client can be imported."""
        from custom_components.carris.api import CarrisApiClient

        assert CarrisApiClient is not None

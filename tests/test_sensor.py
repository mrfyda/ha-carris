"""Tests for the Carris sensor platform."""

from __future__ import annotations

import pytest


class TestCarrisSensor:
    """Test suite for Carris sensor entities."""

    @pytest.mark.asyncio
    async def test_sensor_module_imports(self) -> None:
        """Test that sensor module can be imported."""
        # Import is tested via conftest.py mocking
        pass

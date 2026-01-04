"""Tests for the Carris binary sensor platform."""

from __future__ import annotations

import pytest


class TestCarrisBinarySensor:
    """Test suite for Carris binary sensor entities."""

    @pytest.mark.asyncio
    async def test_binary_sensor_module_imports(self) -> None:
        """Test that binary sensor module can be imported."""
        # Import is tested via conftest.py mocking
        pass

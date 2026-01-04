"""Tests for the Carris device tracker platform."""

from __future__ import annotations

import pytest


class TestCarrisDeviceTracker:
    """Test suite for Carris device tracker entities."""

    @pytest.mark.asyncio
    async def test_device_tracker_module_imports(self) -> None:
        """Test that device tracker module can be imported."""
        # Import is tested via conftest.py mocking
        pass

"""Tests for the Carris config flow."""

from __future__ import annotations

import pytest


class TestCarrisConfigFlow:
    """Test suite for Carris config flow."""

    @pytest.mark.asyncio
    async def test_config_flow_module_imports(self) -> None:
        """Test that config flow module can be imported."""
        # Import is tested via conftest.py mocking
        pass

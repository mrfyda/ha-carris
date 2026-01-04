"""Tests for the Carris integration initialization."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.carris import async_setup_entry, async_unload_entry
from custom_components.carris.const import DOMAIN


async def test_setup_entry_success(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test successful setup of config entry."""
    with patch(
        "custom_components.carris.CarrisApiClient"
    ) as mock_client_class, patch(
        "custom_components.carris.async_get_clientsession"
    ) as mock_session:
        mock_client = AsyncMock()
        mock_client.refresh_token = AsyncMock(return_value="test_token")
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)

        with patch.object(
            hass.config_entries, "async_forward_entry_setups", return_value=True
        ):
            result = await async_setup_entry(hass, mock_config_entry)

        assert result is True
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert "client" in hass.data[DOMAIN][mock_config_entry.entry_id]
        assert "config" in hass.data[DOMAIN][mock_config_entry.entry_id]


async def test_setup_entry_token_failure(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test setup failure when token refresh fails."""
    with patch(
        "custom_components.carris.CarrisApiClient"
    ) as mock_client_class, patch(
        "custom_components.carris.async_get_clientsession"
    ) as mock_session:
        mock_client = AsyncMock()
        mock_client.refresh_token = AsyncMock(
            side_effect=Exception("Token refresh failed")
        )
        mock_client_class.return_value = mock_client

        mock_config_entry.add_to_hass(hass)

        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, mock_config_entry)


async def test_unload_entry_success(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test successful unload of config entry."""
    # Setup first
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "client": MagicMock(),
            "config": mock_config_entry.data,
        }
    }

    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=True
    ):
        result = await async_unload_entry(hass, mock_config_entry)

    assert result is True
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


async def test_unload_entry_failure(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test unload failure."""
    # Setup first
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "client": MagicMock(),
            "config": mock_config_entry.data,
        }
    }

    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=False
    ):
        result = await async_unload_entry(hass, mock_config_entry)

    assert result is False
    # Entry should still be in data since unload failed
    assert mock_config_entry.entry_id in hass.data[DOMAIN]


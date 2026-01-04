"""Tests for the Carris config flow."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.carris.const import (
    CONF_ROUTE_NUMBER,
    CONF_STOP_ID,
    CONF_STOP_LAT,
    CONF_STOP_LNG,
    CONF_STOP_NAME,
    DOMAIN,
    ERROR_STOP_NOT_FOUND,
    ERROR_UNKNOWN,
)


async def test_form_user_step(hass: HomeAssistant) -> None:
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_user_step_stop_not_found(
    hass: HomeAssistant,
) -> None:
    """Test error when stop is not found."""
    with patch(
        "custom_components.carris.config_flow.validate_stop",
        side_effect=ValueError("Stop not found"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STOP_ID: 99999},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == ERROR_STOP_NOT_FOUND


async def test_form_user_step_unknown_error(
    hass: HomeAssistant,
) -> None:
    """Test error when unknown error occurs."""
    with patch(
        "custom_components.carris.config_flow.validate_stop",
        side_effect=Exception("Unknown error"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STOP_ID: 9804},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == ERROR_UNKNOWN


async def test_form_user_step_success_with_routes(
    hass: HomeAssistant,
    mock_stop_info: dict[str, Any],
) -> None:
    """Test successful user step with routes available."""
    with patch(
        "custom_components.carris.config_flow.validate_stop",
        return_value=mock_stop_info,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STOP_ID: 9804},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "route"


async def test_form_user_step_success_no_routes(
    hass: HomeAssistant,
) -> None:
    """Test successful user step with no routes."""
    stop_info_no_routes = {
        "id": 9804,
        "name": "R. D. Fuas Roupinho",
        "location": {"lat": 38.7244087, "lng": -9.1173888},
        "routes": [],
    }

    with patch(
        "custom_components.carris.config_flow.validate_stop",
        return_value=stop_info_no_routes,
    ), patch(
        "custom_components.carris.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STOP_ID: 9804},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Carris - R. D. Fuas Roupinho"
    assert result["data"][CONF_STOP_ID] == 9804
    assert result["data"][CONF_STOP_NAME] == "R. D. Fuas Roupinho"


async def test_form_route_step_select_specific_route(
    hass: HomeAssistant,
    mock_stop_info: dict[str, Any],
) -> None:
    """Test route selection with specific route."""
    with patch(
        "custom_components.carris.config_flow.validate_stop",
        return_value=mock_stop_info,
    ), patch(
        "custom_components.carris.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STOP_ID: 9804},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ROUTE_NUMBER: "742"},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Carris 742 - R. D. Fuas Roupinho"
    assert result["data"][CONF_STOP_ID] == 9804
    assert result["data"][CONF_ROUTE_NUMBER] == "742"
    assert result["data"][CONF_STOP_LAT] == 38.7244087
    assert result["data"][CONF_STOP_LNG] == -9.1173888


async def test_form_route_step_select_all_routes(
    hass: HomeAssistant,
    mock_stop_info: dict[str, Any],
) -> None:
    """Test route selection with all routes."""
    with patch(
        "custom_components.carris.config_flow.validate_stop",
        return_value=mock_stop_info,
    ), patch(
        "custom_components.carris.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_STOP_ID: 9804},
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ROUTE_NUMBER: "all"},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Carris - R. D. Fuas Roupinho"
    assert result["data"][CONF_STOP_ID] == 9804
    assert result["data"][CONF_ROUTE_NUMBER] is None


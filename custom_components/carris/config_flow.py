"""Config flow for Carris integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_STOP_ID,
    CONF_ROUTE_NUMBER,
    CONF_STOP_NAME,
    CONF_STOP_LAT,
    CONF_STOP_LNG,
    ERROR_STOP_NOT_FOUND,
    ERROR_UNKNOWN,
)
from .api import CarrisApiClient, StopInfo

_LOGGER = logging.getLogger(__name__)


async def validate_stop(hass: HomeAssistant, stop_id: int) -> StopInfo:
    """Validate the stop exists and get its info."""
    session = async_get_clientsession(hass)
    client = CarrisApiClient(session)
    
    stop = await client.validate_stop(stop_id)
    if stop is None:
        raise ValueError(f"Stop {stop_id} not found")
    
    return stop


# =============================================================================
# Config Flow
# =============================================================================

class CarrisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Carris."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._stops: list[StopInfo] = []
        self._selected_stop: StopInfo | None = None
        self._available_routes: list[str] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - enter stop ID or search."""
        errors: dict[str, str] = {}

        if user_input is not None:
            stop_id: int = user_input[CONF_STOP_ID]

            try:
                stop_info = await validate_stop(self.hass, stop_id)
                self._selected_stop = stop_info

                # Get available routes at this stop
                routes: list[str] = [
                    r["routeNumber"] for r in stop_info.get("routes", [])
                ]

                if routes:
                    self._available_routes = routes
                    return await self.async_step_route()

                # No routes, just create entry
                location = stop_info.get("location", {})
                return self.async_create_entry(
                    title=f"Carris - {stop_info['name']}",
                    data={
                        CONF_STOP_ID: stop_id,
                        CONF_STOP_NAME: stop_info["name"],
                        CONF_STOP_LAT: location.get("lat"),
                        CONF_STOP_LNG: location.get("lng"),
                    },
                )

            except ValueError:
                errors["base"] = ERROR_STOP_NOT_FOUND
            except Exception:
                _LOGGER.exception("Unexpected error")
                errors["base"] = ERROR_UNKNOWN

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOP_ID): int,
                }
            ),
            errors=errors,
            description_placeholders={
                "example_stops": "9803 (R. D. Fuas Roupinho East), 9804 (R. D. Fuas Roupinho West)"
            },
        )

    async def async_step_route(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle route selection step."""
        if self._selected_stop is None:
            return await self.async_step_user()

        if user_input is not None:
            route: str | None = user_input.get(CONF_ROUTE_NUMBER)

            stop_name: str = self._selected_stop["name"]
            title = f"Carris {route} - {stop_name}" if route and route != "all" else f"Carris - {stop_name}"

            location = self._selected_stop.get("location", {})
            return self.async_create_entry(
                title=title,
                data={
                    CONF_STOP_ID: self._selected_stop["id"],
                    CONF_STOP_NAME: stop_name,
                    CONF_ROUTE_NUMBER: route if route != "all" else None,
                    CONF_STOP_LAT: location.get("lat"),
                    CONF_STOP_LNG: location.get("lng"),
                },
            )

        # Build route options
        route_options: dict[str, str] = {"all": "All routes"}
        for route in self._available_routes:
            route_options[route] = f"Route {route}"

        return self.async_show_form(
            step_id="route",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ROUTE_NUMBER, default="all"): vol.In(route_options),
                }
            ),
            description_placeholders={
                "stop_name": self._selected_stop["name"],
                "routes": ", ".join(self._available_routes),
            },
        )

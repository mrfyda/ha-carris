"""Config flow for Carris integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CarrisApiClient, StopInfo
from .const import (
    CONF_ARRIVAL_THRESHOLD,
    CONF_ROUTE_NUMBER,
    CONF_SCAN_INTERVAL,
    CONF_STOP_ID,
    CONF_STOP_LAT,
    CONF_STOP_LNG,
    CONF_STOP_NAME,
    DEFAULT_ARRIVAL_THRESHOLD,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ERROR_CONNECTION,
    ERROR_STOP_NOT_FOUND,
    ERROR_UNKNOWN,
)

_LOGGER = logging.getLogger(__name__)

# Key for stop search
CONF_STOP_SEARCH = "stop_search"
CONF_STOP_SELECTION = "stop_selection"


async def validate_stop(hass: HomeAssistant, stop_id: int) -> StopInfo:
    """Validate the stop exists and get its info."""
    session = async_get_clientsession(hass)
    client = CarrisApiClient(session)

    stop = await client.validate_stop(stop_id)
    if stop is None:
        raise ValueError(f"Stop {stop_id} not found")

    return stop


async def search_stops(hass: HomeAssistant, query: str) -> list[StopInfo]:
    """Search for stops by name."""
    session = async_get_clientsession(hass)
    client = CarrisApiClient(session)

    all_stops = await client.get_all_stops()
    query_lower = query.lower()

    # Filter stops by name containing the query
    matching_stops = [stop for stop in all_stops if query_lower in stop.get("name", "").lower()]

    # Sort by name and limit results
    matching_stops.sort(key=lambda s: s.get("name", ""))
    return matching_stops[:20]  # Limit to 20 results


# =============================================================================
# Config Flow
# =============================================================================


class CarrisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Carris."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._stops: list[StopInfo] = []
        self._selected_stop: StopInfo | None = None
        self._available_routes: list[str] = []
        self._search_results: list[StopInfo] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return CarrisOptionsFlowHandler(config_entry)

    async def async_step_user(self, _user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step - choose search or manual entry."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["search", "manual"],
        )

    async def async_step_search(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle stop search by name."""
        errors: dict[str, str] = {}

        if user_input is not None:
            search_query = user_input.get(CONF_STOP_SEARCH, "")

            if search_query:
                try:
                    self._search_results = await search_stops(self.hass, search_query)

                    if self._search_results:
                        return await self.async_step_select_stop()
                    else:
                        errors["base"] = ERROR_STOP_NOT_FOUND
                except Exception:
                    _LOGGER.exception("Error searching stops")
                    errors["base"] = ERROR_CONNECTION

        return self.async_show_form(
            step_id="search",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOP_SEARCH): str,
                }
            ),
            errors=errors,
        )

    async def async_step_select_stop(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle stop selection from search results."""
        if user_input is not None:
            stop_id = int(user_input[CONF_STOP_SELECTION])

            # Find the selected stop
            for stop in self._search_results:
                if stop.get("id") == stop_id:
                    self._selected_stop = stop
                    break

            if self._selected_stop:
                # Get available routes at this stop
                routes: list[str] = [
                    r["routeNumber"] for r in self._selected_stop.get("routes", [])
                ]

                if routes:
                    self._available_routes = routes
                    return await self.async_step_route()

                # No routes, just create entry
                location = self._selected_stop.get("location", {})
                return self.async_create_entry(
                    title=f"Carris - {self._selected_stop['name']}",
                    data={
                        CONF_STOP_ID: stop_id,
                        CONF_STOP_NAME: self._selected_stop["name"],
                        CONF_STOP_LAT: location.get("lat"),
                        CONF_STOP_LNG: location.get("lng"),
                    },
                )

        # Build stop options from search results
        stop_options: dict[str, str] = {}
        for stop in self._search_results:
            stop_id = stop.get("id", 0)
            stop_name = stop.get("name", "Unknown")
            routes_str = ", ".join(r["routeNumber"] for r in stop.get("routes", [])[:3])
            label = f"{stop_name} (ID: {stop_id})"
            if routes_str:
                label += f" - Routes: {routes_str}"
            stop_options[str(stop_id)] = label

        return self.async_show_form(
            step_id="select_stop",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOP_SELECTION): vol.In(stop_options),
                }
            ),
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual stop ID entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            stop_id: int = user_input[CONF_STOP_ID]

            try:
                stop_info = await validate_stop(self.hass, stop_id)
                self._selected_stop = stop_info

                # Get available routes at this stop
                routes: list[str] = [r["routeNumber"] for r in stop_info.get("routes", [])]

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
            step_id="manual",
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

    async def async_step_route(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle route selection step."""
        if self._selected_stop is None:
            return await self.async_step_user()

        if user_input is not None:
            route: str | None = user_input.get(CONF_ROUTE_NUMBER)

            stop_name: str = self._selected_stop["name"]
            title = (
                f"Carris {route} - {stop_name}"
                if route and route != "all"
                else f"Carris - {stop_name}"
            )

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


# =============================================================================
# Options Flow
# =============================================================================


class CarrisOptionsFlowHandler(OptionsFlow):
    """Handle Carris options flow."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options or defaults
        scan_interval = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        arrival_threshold = self.config_entry.options.get(
            CONF_ARRIVAL_THRESHOLD, DEFAULT_ARRIVAL_THRESHOLD
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=scan_interval,
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=300)),
                    vol.Optional(
                        CONF_ARRIVAL_THRESHOLD,
                        default=arrival_threshold,
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
                }
            ),
        )

"""Carris Bus integration for Home Assistant."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BusArrivalResponse, BusSnapshotItem, CarrisApiClient
from .const import (
    CONF_ROUTE_NUMBER,
    CONF_SCAN_INTERVAL,
    CONF_STOP_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.DEVICE_TRACKER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Carris from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Create API client
    session = async_get_clientsession(hass)
    client = CarrisApiClient(session)

    # Get initial token - raise ConfigEntryNotReady if this fails
    try:
        await client.refresh_token()
    except Exception as err:
        _LOGGER.error("Failed to get Carris API token: %s", err)
        raise ConfigEntryNotReady(f"Failed to connect to Carris API: {err}") from err

    stop_id: int = entry.data[CONF_STOP_ID]
    route_number: str | None = entry.data.get(CONF_ROUTE_NUMBER)

    # Get scan interval from options or use default
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    arrival_scan_interval = timedelta(seconds=scan_interval)
    bus_position_scan_interval = timedelta(seconds=scan_interval // 2)

    # Create arrival coordinator (shared by sensor and binary_sensor)
    async def async_update_arrivals() -> list[BusArrivalResponse]:
        """Fetch arrival data from API."""
        try:
            result = await client.get_next_buses(stop_id)
            _LOGGER.debug("Carris API returned %d arrivals", len(result) if result else 0)
            return result
        except Exception as err:
            _LOGGER.warning("Failed to fetch Carris arrivals: %s", err)
            raise UpdateFailed(f"Failed to fetch arrivals: {err}") from err

    arrival_coordinator: DataUpdateCoordinator[list[BusArrivalResponse]] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"carris_{stop_id}_arrivals",
        update_method=async_update_arrivals,
        update_interval=arrival_scan_interval,
    )

    # Create bus position coordinator (for device_tracker, only if route specified)
    bus_coordinator: DataUpdateCoordinator[list[BusSnapshotItem]] | None = None
    direction: int | None = None

    if route_number:
        # Detect direction for this stop/route
        direction = await client.get_direction_for_stop(route_number, stop_id)
        if direction:
            _LOGGER.info(
                "Detected direction %d for route %s at stop %d", direction, route_number, stop_id
            )

        async def async_update_bus_positions() -> list[BusSnapshotItem]:
            """Fetch bus positions from API."""
            try:
                result = await client.get_buses_for_route(route_number, direction)
                _LOGGER.debug(
                    "Carris API returned %d buses for route %s",
                    len(result) if result else 0,
                    route_number,
                )
                return result
            except Exception as err:
                _LOGGER.warning("Failed to fetch Carris bus positions: %s", err)
                raise UpdateFailed(f"Failed to fetch bus positions: {err}") from err

        bus_coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"carris_{stop_id}_{route_number}_buses",
            update_method=async_update_bus_positions,
            update_interval=bus_position_scan_interval,
        )

    # Perform initial refresh
    await arrival_coordinator.async_config_entry_first_refresh()
    if bus_coordinator:
        await bus_coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "config": entry.data,
        "arrival_coordinator": arrival_coordinator,
        "bus_coordinator": bus_coordinator,
        "direction": direction,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

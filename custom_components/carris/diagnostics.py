"""Diagnostics support for Carris integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {
    "latitude",
    "longitude",
    "lat",
    "lng",
    "stop_lat",
    "stop_lng",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = hass.data[DOMAIN].get(entry.entry_id, {})

    arrival_coordinator = data.get("arrival_coordinator")
    bus_coordinator = data.get("bus_coordinator")

    diagnostics_data: dict[str, Any] = {
        "config_entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "coordinators": {
            "arrival_coordinator": {
                "name": arrival_coordinator.name if arrival_coordinator else None,
                "last_update_success": (
                    arrival_coordinator.last_update_success if arrival_coordinator else None
                ),
                "update_interval": (
                    str(arrival_coordinator.update_interval) if arrival_coordinator else None
                ),
                "data_count": (
                    len(arrival_coordinator.data)
                    if arrival_coordinator and arrival_coordinator.data
                    else 0
                ),
            },
            "bus_coordinator": {
                "name": bus_coordinator.name if bus_coordinator else None,
                "last_update_success": (
                    bus_coordinator.last_update_success if bus_coordinator else None
                ),
                "update_interval": (
                    str(bus_coordinator.update_interval) if bus_coordinator else None
                ),
                "data_count": (
                    len(bus_coordinator.data) if bus_coordinator and bus_coordinator.data else 0
                ),
            }
            if bus_coordinator
            else None,
        },
        "direction": data.get("direction"),
    }

    # Add sample arrival data (redacted)
    if arrival_coordinator and arrival_coordinator.data:
        sample_arrivals = []
        for arrival in arrival_coordinator.data[:3]:  # First 3 arrivals
            sample_arrivals.append(
                {
                    "routeNumber": arrival.get("routeNumber"),
                    "destination": arrival.get("destination"),
                    "stopTime": arrival.get("stopTime"),
                }
            )
        diagnostics_data["sample_arrivals"] = sample_arrivals

    # Add sample bus data (redacted)
    if bus_coordinator and bus_coordinator.data:
        sample_buses = []
        for bus in bus_coordinator.data[:3]:  # First 3 buses
            sample_buses.append(
                {
                    "route": bus.get("route"),
                    "plate": bus.get("plate"),
                    "direction": bus.get("direction"),
                    "state": bus.get("state"),
                }
            )
        diagnostics_data["sample_buses"] = sample_buses

    return diagnostics_data

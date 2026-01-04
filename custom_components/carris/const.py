"""Constants for Carris integration."""

from __future__ import annotations

from typing import Final

# =============================================================================
# Domain
# =============================================================================
DOMAIN: Final = "carris"

# =============================================================================
# API Configuration
# =============================================================================
API_KEY: Final = "8844d854-9c37-4f22-b4d4-50a3626da5da"
BASE_URL: Final = "https://gateway.carris.pt/gateway/sitecarris"
TOKEN_ENDPOINT: Final = f"{BASE_URL}/token"
STOPS_ENDPOINT: Final = f"{BASE_URL}/busstops/getnextroutesatstop"
ALL_STOPS_ENDPOINT: Final = f"{BASE_URL}/busstops/getall"
VEHICLES_SNAPSHOT_ENDPOINT: Final = f"{BASE_URL}/vehicles/getsnapshot"

# =============================================================================
# Config Keys
# =============================================================================
CONF_STOP_ID: Final = "stop_id"
CONF_ROUTE_NUMBER: Final = "route_number"
CONF_ROUTES: Final = "routes"  # List of all routes serving the stop
CONF_STOP_NAME: Final = "stop_name"
CONF_STOP_LAT: Final = "stop_lat"
CONF_STOP_LNG: Final = "stop_lng"

# =============================================================================
# Options Keys
# =============================================================================
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_ARRIVAL_THRESHOLD: Final = "arrival_threshold"
CONF_WALK_TIME: Final = "walk_time"

# =============================================================================
# Defaults
# =============================================================================
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds (1 minute)
DEFAULT_ARRIVAL_THRESHOLD: Final = 5  # minutes for "arriving soon" binary sensor
DEFAULT_WALK_TIME: Final = 0  # minutes - time to walk to bus stop (0 = disabled)
DEFAULT_API_TIMEOUT: Final = 30  # seconds
TOKEN_REFRESH_INTERVAL: Final = 43200  # seconds (12 hours)

# =============================================================================
# Device Info
# =============================================================================
MANUFACTURER: Final = "Carris"
MODEL_BUS_STOP: Final = "Bus Stop"

# =============================================================================
# Error Messages (for translation keys)
# =============================================================================
ERROR_STOP_NOT_FOUND: Final = "stop_not_found"
ERROR_CONNECTION: Final = "cannot_connect"
ERROR_UNKNOWN: Final = "unknown"
ERROR_AUTH_FAILED: Final = "auth_failed"

# =============================================================================
# Attribution
# =============================================================================
ATTRIBUTION: Final = "Data provided by Carris"

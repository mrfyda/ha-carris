"""Carris API client.

This module contains a pure Python API client for the Carris bus service.
It has no Home Assistant dependencies and can be used independently.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict

import aiohttp
import async_timeout

from .const import (
    API_KEY,
    BASE_URL,
    TOKEN_ENDPOINT,
    VEHICLES_SNAPSHOT_ENDPOINT,
    DEFAULT_API_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

# Refresh token 1 hour before expiry
TOKEN_REFRESH_BUFFER = timedelta(hours=1)

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 30.0  # seconds


# =============================================================================
# Type Definitions for API Responses
# =============================================================================

class BusArrivalResponse(TypedDict):
    """Type for bus arrival API response."""

    routeNumber: str
    stopId: int
    stopTime: str
    destination: str


class BusPathPoint(TypedDict):
    """Type for a point in the bus path."""

    lat: float
    lng: float
    bearing: int
    msToNext: int


class BusSnapshotItem(TypedDict, total=False):
    """Type for individual bus in vehicle snapshot.
    
    Based on actual Carris API response structure.
    """

    route: str  # Route number (e.g., "742")
    plate: str  # License plate (e.g., "4Z758")
    type: int   # Vehicle type ID
    zone: int   # Zone ID
    id: int     # Vehicle ID
    state: int  # Vehicle state
    path: list[BusPathPoint]  # Position history (first is most recent)
    version: int
    direction: int  # Direction (1 or 2)
    variantNumber: int


class TokenResponse(TypedDict):
    """Type for token API response."""

    access_token: str
    token_type: str
    expires_in: int


class RouteInfo(TypedDict):
    """Type for route information."""

    routeNumber: str
    color: str


class LocationInfo(TypedDict):
    """Type for location information."""

    lat: float
    lng: float


class StopInfo(TypedDict, total=False):
    """Type for bus stop information."""

    id: int
    name: str
    location: LocationInfo
    routes: list[RouteInfo]


# =============================================================================
# API Client
# =============================================================================

class CarrisApiClient:
    """API client for Carris.
    
    This client handles authentication and provides methods to interact
    with the Carris API. It automatically refreshes tokens when needed.
    
    Example usage:
        async with aiohttp.ClientSession() as session:
            client = CarrisApiClient(session)
            await client.refresh_token()
            buses = await client.get_next_buses(9804)
            print(buses)
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client.
        
        Args:
            session: An aiohttp ClientSession for making HTTP requests.
        """
        self._session = session
        self._token: str | None = None
        self._token_expires_at: datetime | None = None

    @property
    def has_token(self) -> bool:
        """Check if a token is available."""
        return self._token is not None

    @property
    def token_is_expired(self) -> bool:
        """Check if the token is expired or about to expire."""
        if self._token is None or self._token_expires_at is None:
            return True
        # Consider expired if within the refresh buffer
        return datetime.now(timezone.utc) >= (self._token_expires_at - TOKEN_REFRESH_BUFFER)

    async def refresh_token(self) -> str:
        """Get a new API token.
        
        Returns:
            The new access token.
            
        Raises:
            aiohttp.ClientError: If the request fails.
        """
        headers = {"X-Gravitee-Api-Key": API_KEY}

        async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
            async with self._session.post(TOKEN_ENDPOINT, headers=headers) as response:
                response.raise_for_status()
                data: TokenResponse = await response.json()
                self._token = data["access_token"]
                # Calculate expiry time
                expires_in = data.get("expires_in", 86400)  # Default to 24 hours
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                _LOGGER.debug(
                    "Carris token refreshed, expires at %s",
                    self._token_expires_at.isoformat()
                )
                return self._token

    async def _ensure_valid_token(self) -> None:
        """Ensure we have a valid token, refreshing if needed."""
        if self.token_is_expired:
            _LOGGER.debug("Token expired or missing, refreshing...")
            await self.refresh_token()

    def _get_auth_headers(self) -> dict[str, str]:
        """Get headers with authentication."""
        return {
            "X-Gravitee-Api-Key": API_KEY,
            "Authorization": f"Bearer {self._token}",
        }

    async def _request_with_retry(
        self, url: str, headers: dict[str, str]
    ) -> Any:
        """Make a GET request with exponential backoff retry.
        
        Args:
            url: The URL to request.
            headers: Request headers (will be modified on retry).
            
        Returns:
            The JSON response data.
            
        Raises:
            aiohttp.ClientError: If the request fails after all retries.
            asyncio.TimeoutError: If the request times out.
        """
        import asyncio
        
        last_exception: Exception | None = None
        delay = INITIAL_RETRY_DELAY
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with async_timeout.timeout(DEFAULT_API_TIMEOUT):
                    async with self._session.get(url, headers=headers) as response:
                        if response.status == 401:
                            # Token expired, refresh and retry immediately
                            _LOGGER.debug("Got 401, refreshing token...")
                            await self.refresh_token()
                            headers["Authorization"] = f"Bearer {self._token}"
                            async with self._session.get(url, headers=headers) as retry_response:
                                retry_response.raise_for_status()
                                return await retry_response.json()
                        
                        if response.status == 429:
                            # Rate limited, use exponential backoff
                            retry_after = response.headers.get("Retry-After")
                            wait_time = float(retry_after) if retry_after else delay
                            _LOGGER.warning(
                                "Rate limited, waiting %s seconds before retry",
                                wait_time
                            )
                            await asyncio.sleep(wait_time)
                            delay = min(delay * 2, MAX_RETRY_DELAY)
                            continue
                        
                        if response.status >= 500:
                            # Server error, retry with backoff
                            _LOGGER.warning(
                                "Server error %d on attempt %d, retrying in %s seconds",
                                response.status, attempt + 1, delay
                            )
                            await asyncio.sleep(delay)
                            delay = min(delay * 2, MAX_RETRY_DELAY)
                            continue
                        
                        response.raise_for_status()
                        return await response.json()
                        
            except asyncio.TimeoutError as err:
                last_exception = err
                if attempt < MAX_RETRIES:
                    _LOGGER.warning(
                        "Timeout on attempt %d, retrying in %s seconds",
                        attempt + 1, delay
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, MAX_RETRY_DELAY)
                else:
                    _LOGGER.error("Request timed out after %d attempts", MAX_RETRIES + 1)
                    raise
                    
            except aiohttp.ClientConnectionError as err:
                last_exception = err
                if attempt < MAX_RETRIES:
                    _LOGGER.warning(
                        "Connection error on attempt %d: %s, retrying in %s seconds",
                        attempt + 1, err, delay
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, MAX_RETRY_DELAY)
                else:
                    _LOGGER.error(
                        "Connection failed after %d attempts: %s",
                        MAX_RETRIES + 1, err
                    )
                    raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise aiohttp.ClientError("Request failed after all retries")

    async def get_next_buses(self, stop_id: int) -> list[BusArrivalResponse]:
        """Get next buses at a stop.
        
        Args:
            stop_id: The bus stop ID.
            
        Returns:
            List of upcoming bus arrivals.
        """
        await self._ensure_valid_token()

        headers = self._get_auth_headers()
        url = f"{BASE_URL}/busstops/getnextroutesatstop?stopIds={stop_id}"
        return await self._request_with_retry(url, headers)

    async def get_all_stops(self) -> list[StopInfo]:
        """Get all bus stops.
        
        Returns:
            List of all bus stops with their information.
        """
        await self._ensure_valid_token()

        headers = self._get_auth_headers()
        url = f"{BASE_URL}/busstops/getall"
        return await self._request_with_retry(url, headers)

    async def get_bus_snapshot(self) -> list[BusSnapshotItem]:
        """Get real-time positions of all buses.
        
        Returns:
            List of bus positions. Empty list if request fails.
        """
        await self._ensure_valid_token()

        headers = self._get_auth_headers()
        url = f"{VEHICLES_SNAPSHOT_ENDPOINT}?culture=pt-PT"
        
        try:
            result = await self._request_with_retry(url, headers)
            
            # Log response summary for debugging
            if result and isinstance(result, list):
                _LOGGER.debug("Vehicle snapshot: %d buses", len(result))
            
            # Handle different response formats
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                # Some APIs wrap the array in an object
                for key in ["vehicles", "data", "items", "result"]:
                    if key in result and isinstance(result[key], list):
                        return result[key]
                _LOGGER.warning("Unknown vehicle snapshot format: %s", list(result.keys()))
                return []
            else:
                _LOGGER.warning("Unexpected vehicle snapshot type: %s", type(result))
                return []
        except Exception as err:
            _LOGGER.warning("Failed to get bus snapshot: %s", err)
            return []

    async def get_buses_for_route(
        self, route_number: str, direction: int | None = None
    ) -> list[BusSnapshotItem]:
        """Get real-time positions of buses for a specific route.
        
        Args:
            route_number: The route number to filter by.
            direction: Optional direction (1 or 2) to filter by.
            
        Returns:
            List of bus positions for the specified route.
        """
        snapshot = await self.get_bus_snapshot()
        
        if not snapshot:
            return []
        
        # Filter by route number
        matching_buses = [
            bus for bus in snapshot
            if isinstance(bus, dict) and bus.get("route") == route_number
        ]
        
        # Filter by direction if specified
        if direction is not None:
            matching_buses = [
                bus for bus in matching_buses
                if bus.get("direction") == direction
            ]
        
        _LOGGER.debug(
            "Found %d buses for route %s (direction=%s) out of %d total",
            len(matching_buses), route_number, direction, len(snapshot)
        )
        
        return matching_buses

    async def get_direction_for_stop(
        self, route_number: str, stop_id: int
    ) -> int | None:
        """Detect which direction serves a specific stop.
        
        Args:
            route_number: The route number.
            stop_id: The stop ID.
            
        Returns:
            Direction (1 or 2) that serves this stop, or None if not found.
        """
        await self._ensure_valid_token()
        
        headers = self._get_auth_headers()
        
        # Get today's date
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Try direction 1
        url = f"{BASE_URL}/routes/getbusstoptimes?routeNumber={route_number}&stopId={stop_id}&direction=1&date={today}"
        try:
            result = await self._request_with_retry(url, headers)
            if isinstance(result, dict) and len(result.get("stopTimes", [])) > 0:
                _LOGGER.debug("Direction 1 serves stop %d on route %s", stop_id, route_number)
                return 1
        except Exception:
            pass
        
        # Try direction 2
        url = f"{BASE_URL}/routes/getbusstoptimes?routeNumber={route_number}&stopId={stop_id}&direction=2&date={today}"
        try:
            result = await self._request_with_retry(url, headers)
            if isinstance(result, dict) and len(result.get("stopTimes", [])) > 0:
                _LOGGER.debug("Direction 2 serves stop %d on route %s", stop_id, route_number)
                return 2
        except Exception:
            pass
        
        _LOGGER.warning(
            "Could not determine direction for route %s at stop %d",
            route_number, stop_id
        )
        return None

    async def validate_stop(self, stop_id: int) -> StopInfo | None:
        """Validate a stop exists and get its info.
        
        Args:
            stop_id: The stop ID to validate.
            
        Returns:
            The stop info if found, None otherwise.
        """
        stops = await self.get_all_stops()
        
        for stop in stops:
            if stop.get("id") == stop_id:
                return stop
        
        return None


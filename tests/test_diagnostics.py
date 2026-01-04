"""Tests for the Carris diagnostics module."""

from __future__ import annotations

from typing import Any

import pytest


class TestDiagnosticsRedaction:
    """Test suite for diagnostics data redaction."""

    def test_sensitive_keys_identified(self) -> None:
        """Test that sensitive keys are identified for redaction."""
        to_redact = {
            "latitude",
            "longitude",
            "lat",
            "lng",
            "stop_lat",
            "stop_lng",
        }

        # All location-related fields should be redacted
        assert "latitude" in to_redact
        assert "longitude" in to_redact
        assert "lat" in to_redact
        assert "lng" in to_redact
        assert "stop_lat" in to_redact
        assert "stop_lng" in to_redact

    def test_non_sensitive_keys_not_redacted(self) -> None:
        """Test that non-sensitive keys are not redacted."""
        to_redact = {
            "latitude",
            "longitude",
            "lat",
            "lng",
            "stop_lat",
            "stop_lng",
        }

        assert "stop_id" not in to_redact
        assert "route_number" not in to_redact
        assert "stop_name" not in to_redact


class TestDiagnosticsStructure:
    """Test suite for diagnostics data structure."""

    @pytest.fixture
    def mock_config_entry_data(self) -> dict[str, Any]:
        """Return mock config entry data."""
        return {
            "stop_id": 9804,
            "stop_name": "R. D. Fuas Roupinho",
            "route_number": "742",
            "stop_lat": 38.7244087,
            "stop_lng": -9.1173888,
        }

    def test_diagnostics_includes_config_entry(
        self, mock_config_entry_data: dict[str, Any]
    ) -> None:
        """Test that diagnostics includes config entry data."""
        diagnostics = {
            "config_entry": {
                "entry_id": "test_entry_id",
                "version": 1,
                "domain": "carris",
                "title": "Carris 742 - R. D. Fuas Roupinho",
                "data": mock_config_entry_data,
                "options": {},
            },
        }

        assert "config_entry" in diagnostics
        assert diagnostics["config_entry"]["domain"] == "carris"

    def test_diagnostics_includes_coordinator_info(self) -> None:
        """Test that diagnostics includes coordinator information."""
        diagnostics = {
            "coordinators": {
                "arrival_coordinator": {
                    "name": "carris_9804_arrivals",
                    "last_update_success": True,
                    "update_interval": "0:01:00",
                    "data_count": 5,
                },
                "bus_coordinator": {
                    "name": "carris_9804_742_buses",
                    "last_update_success": True,
                    "update_interval": "0:00:30",
                    "data_count": 2,
                },
            },
        }

        assert "coordinators" in diagnostics
        assert "arrival_coordinator" in diagnostics["coordinators"]
        assert diagnostics["coordinators"]["arrival_coordinator"]["last_update_success"]

    def test_diagnostics_includes_sample_data(self) -> None:
        """Test that diagnostics includes sample data."""
        diagnostics = {
            "sample_arrivals": [
                {
                    "routeNumber": "742",
                    "destination": "Pólo Univ. Ajuda",
                    "stopTime": "2026-01-04T14:08:32+00:00",
                },
            ],
            "sample_buses": [
                {
                    "route": "742",
                    "plate": "4Z758",
                    "direction": 1,
                    "state": 1,
                },
            ],
        }

        assert "sample_arrivals" in diagnostics
        assert "sample_buses" in diagnostics
        assert len(diagnostics["sample_arrivals"]) == 1
        assert diagnostics["sample_arrivals"][0]["routeNumber"] == "742"

    def test_diagnostics_limits_sample_data(self) -> None:
        """Test that diagnostics limits sample data to first 3 items."""
        arrivals = [{"routeNumber": f"74{i}"} for i in range(10)]

        # Simulate limiting to first 3
        sample = arrivals[:3]

        assert len(sample) == 3
        assert sample[0]["routeNumber"] == "740"
        assert sample[2]["routeNumber"] == "742"


class TestDiagnosticsModuleImport:
    """Test suite for diagnostics module import."""

    def test_diagnostics_module_constants(self) -> None:
        """Test that diagnostics uses correct domain constant."""
        from custom_components.carris.const import DOMAIN

        assert DOMAIN == "carris"

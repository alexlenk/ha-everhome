"""Test Everhome data coordinator."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.everhome.const import DOMAIN, UPDATE_INTERVAL
from custom_components.everhome.coordinator import (
    EverhomeDataUpdateCoordinator,
)


class TestEverhomeDataUpdateCoordinator:
    """Test Everhome data update coordinator."""

    @pytest.fixture
    def mock_auth(self):
        """Mock EverhomeAuth."""
        auth = AsyncMock()
        auth.async_get_access_token.return_value = "test_access_token"
        auth.aiohttp_session = AsyncMock()
        return auth

    @pytest.fixture
    def coordinator(self, hass: HomeAssistant, mock_auth, mock_config_entry):
        """Create coordinator fixture."""
        return EverhomeDataUpdateCoordinator(hass, mock_auth, mock_config_entry)

    def test_coordinator_initialization(
        self, hass: HomeAssistant, mock_auth, mock_config_entry
    ):
        """Test coordinator initialization."""
        coordinator = EverhomeDataUpdateCoordinator(hass, mock_auth, mock_config_entry)

        assert coordinator.auth == mock_auth
        assert coordinator.hass == hass
        assert coordinator.entry == mock_config_entry
        assert coordinator.name == DOMAIN
        assert coordinator.update_interval == timedelta(seconds=UPDATE_INTERVAL)
        assert coordinator._devices == {}

    async def test_update_data_success(
        self, coordinator, mock_auth, mock_shutter_device, mock_awning_device
    ):
        """Test successful data update."""
        # Mock API response with shutter devices
        devices_data = [
            {**mock_shutter_device, "subtype": "shutter"},
            {**mock_awning_device, "subtype": "awning"},
            {"id": "light_001", "subtype": "light"},  # Should be filtered out
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = devices_data

        mock_auth.aiohttp_session.get.return_value.__aenter__.return_value = (
            mock_response
        )

        result = await coordinator._async_update_data()

        # Should only include shutter-type devices
        assert len(result) == 2
        assert "shutter_001" in result
        assert "awning_001" in result
        assert "light_001" not in result

        # Verify API was called correctly
        mock_auth.async_get_access_token.assert_called_once()
        mock_auth.aiohttp_session.get.assert_called_once()

    async def test_update_data_auth_failed(self, coordinator, mock_auth):
        """Test data update with auth failure."""
        mock_auth.async_get_access_token.side_effect = ConfigEntryAuthFailed(
            "Auth failed"
        )

        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_update_data_client_error(self, coordinator, mock_auth):
        """Test data update with client error."""
        mock_auth.async_get_access_token.side_effect = aiohttp.ClientError(
            "Connection failed"
        )

        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()

    async def test_update_data_timeout_error(self, coordinator, mock_auth):
        """Test data update with timeout error."""
        mock_auth.async_get_access_token.side_effect = asyncio.TimeoutError()

        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()

    async def test_get_devices_http_error(self, coordinator, mock_auth):
        """Test get devices with HTTP error response."""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal Server Error"

        mock_auth.aiohttp_session.get.return_value.__aenter__.return_value = (
            mock_response
        )

        with pytest.raises(UpdateFailed, match="Failed to get devices: 500"):
            await coordinator._get_devices()

    async def test_get_devices_filters_device_types(self, coordinator, mock_auth):
        """Test that get_devices properly filters device types."""
        devices_data = [
            {"id": "shutter_001", "subtype": "shutter"},
            {"id": "blind_001", "subtype": "blind"},
            {"id": "awning_001", "subtype": "awning"},
            {"id": "curtain_001", "subtype": "curtain"},
            {"id": "garage_001", "subtype": "garage_door"},
            {"id": "light_001", "subtype": "light"},
            {"id": "switch_001", "subtype": "switch"},
            {"id": "no_subtype", "name": "No subtype device"},
        ]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = devices_data

        mock_auth.aiohttp_session.get.return_value.__aenter__.return_value = (
            mock_response
        )

        result = await coordinator._get_devices()

        # Should only include shutter-type devices
        expected_devices = [
            "shutter_001",
            "blind_001",
            "awning_001",
            "curtain_001",
            "garage_001",
        ]
        assert len(result) == 5
        for device_id in expected_devices:
            assert device_id in result

        # Should not include non-shutter devices
        assert "light_001" not in result
        assert "switch_001" not in result
        assert "no_subtype" not in result

    async def test_execute_device_action_success(self, coordinator, mock_auth):
        """Test successful device action execution."""
        mock_response = AsyncMock()
        mock_response.status = 200

        mock_auth.aiohttp_session.post.return_value.__aenter__.return_value = (
            mock_response
        )

        result = await coordinator.execute_device_action("device_001", "open")

        assert result is True

        # Verify API call
        mock_auth.async_get_access_token.assert_called_once()
        mock_auth.aiohttp_session.post.assert_called_once()

        # Check call arguments
        call_args = mock_auth.aiohttp_session.post.call_args
        assert "device_001" in call_args[0][0]  # URL contains device ID
        assert call_args[1]["json"] == {"action": "open"}

        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert "Content-Type" in headers

    async def test_execute_device_action_http_error(self, coordinator, mock_auth):
        """Test device action execution with HTTP error."""
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"

        mock_auth.aiohttp_session.post.return_value.__aenter__.return_value = (
            mock_response
        )

        result = await coordinator.execute_device_action("device_001", "invalid_action")

        assert result is False

    async def test_execute_device_action_client_error(self, coordinator, mock_auth):
        """Test device action execution with client error."""
        mock_auth.aiohttp_session.post.side_effect = aiohttp.ClientError(
            "Connection failed"
        )

        result = await coordinator.execute_device_action("device_001", "open")

        assert result is False

    async def test_execute_device_action_timeout_error(self, coordinator, mock_auth):
        """Test device action execution with timeout error."""
        mock_auth.aiohttp_session.post.side_effect = asyncio.TimeoutError()

        result = await coordinator.execute_device_action("device_001", "open")

        assert result is False

    async def test_execute_device_action_auth_token_refresh(
        self, coordinator, mock_auth
    ):
        """Test device action execution triggers token refresh."""
        mock_response = AsyncMock()
        mock_response.status = 200

        mock_auth.aiohttp_session.post.return_value.__aenter__.return_value = (
            mock_response
        )
        mock_auth.async_get_access_token.return_value = "refreshed_token"

        await coordinator.execute_device_action("device_001", "close")

        # Verify token was requested
        mock_auth.async_get_access_token.assert_called_once()

        # Verify correct headers were used
        call_args = mock_auth.aiohttp_session.post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer refreshed_token"

    async def test_get_devices_empty_response(self, coordinator, mock_auth):
        """Test get devices with empty response."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = []

        mock_auth.aiohttp_session.get.return_value.__aenter__.return_value = (
            mock_response
        )

        result = await coordinator._get_devices()

        assert result == {}

    async def test_coordinator_api_url_construction(self, coordinator, mock_auth):
        """Test that coordinator constructs correct API URLs."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = []

        mock_auth.aiohttp_session.get.return_value.__aenter__.return_value = (
            mock_response
        )

        await coordinator._get_devices()

        # Verify correct URL was called
        call_args = mock_auth.aiohttp_session.get.call_args
        expected_url = "https://everhome.cloud/device"
        assert call_args[0][0] == expected_url

    async def test_execute_action_url_construction(self, coordinator, mock_auth):
        """Test that execute action constructs correct URLs."""
        mock_response = AsyncMock()
        mock_response.status = 200

        mock_auth.aiohttp_session.post.return_value.__aenter__.return_value = (
            mock_response
        )

        await coordinator.execute_device_action("test_device_123", "stop")

        # Verify correct URL was called
        call_args = mock_auth.aiohttp_session.post.call_args
        expected_url = "https://everhome.cloud/device/test_device_123/execute"
        assert call_args[0][0] == expected_url

        # Verify correct payload
        assert call_args[1]["json"] == {"action": "stop"}

    async def test_coordinator_device_caching(
        self, coordinator, mock_auth, mock_shutter_device
    ):
        """Test that coordinator properly manages device cache."""
        devices_data = [{**mock_shutter_device, "subtype": "shutter"}]

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = devices_data

        mock_auth.aiohttp_session.get.return_value.__aenter__.return_value = (
            mock_response
        )

        # First call
        result1 = await coordinator._get_devices()
        assert "shutter_001" in result1

        # Second call - should make new API call (no caching in _get_devices)
        result2 = await coordinator._get_devices()
        assert "shutter_001" in result2

        # Verify API was called twice
        assert mock_auth.aiohttp_session.get.call_count == 2

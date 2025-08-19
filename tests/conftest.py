"""Fixtures for Everhome integration tests."""

from __future__ import annotations

import json
from typing import Any, Dict
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

pytest_plugins = "pytest_homeassistant_custom_component"

from custom_components.everhome.const import (
    CONF_ACCESS_TOKEN,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_REFRESH_TOKEN,
    CONF_TOKEN_EXPIRY,
    DOMAIN,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_CLIENT_ID: "test_client_id",
            CONF_CLIENT_SECRET: "test_client_secret",
            CONF_ACCESS_TOKEN: "test_access_token",
            CONF_REFRESH_TOKEN: "test_refresh_token",
            CONF_TOKEN_EXPIRY: 1234567890,
        },
        entry_id="test_entry_id",
        unique_id="everhome_test",
        title="Everhome",
    )


@pytest.fixture
def mock_oauth_config() -> Dict[str, Any]:
    """Mock OAuth configuration."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "redirect_uri": "https://my.home-assistant.io/redirect/oauth",
    }


@pytest.fixture
def mock_token_response() -> Dict[str, Any]:
    """Mock OAuth token response."""
    return {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


@pytest.fixture
def mock_shutter_device() -> Dict[str, Any]:
    """Mock shutter device response."""
    return {
        "id": "shutter_001",
        "name": "Bedroom Shutter",
        "type": "cover",
        "categories": ["shutter"],
        "traits": ["openclose", "startstop"],
        "willReportState": True,
        "attributes": {
            "openDirection": ["UP", "DOWN"],
        },
        "state": {
            "online": True,
            "openPercent": 0,
            "openState": ["CLOSED"],
        },
        "deviceInfo": {
            "manufacturer": "Everhome",
            "model": "Smart Shutter",
            "hwVersion": "1.0",
            "swVersion": "2.1.0",
        },
    }


@pytest.fixture
def mock_awning_device() -> Dict[str, Any]:
    """Mock awning device response."""
    return {
        "id": "awning_001",
        "name": "Patio Awning",
        "type": "cover",
        "categories": ["awning"],
        "traits": ["openclose", "startstop"],
        "willReportState": True,
        "attributes": {
            "openDirection": ["OUT", "IN"],
        },
        "state": {
            "online": True,
            "openPercent": 50,
            "openState": ["OPEN"],
        },
        "deviceInfo": {
            "manufacturer": "Everhome",
            "model": "Smart Awning",
            "hwVersion": "1.0",
            "swVersion": "2.1.0",
        },
    }


@pytest.fixture
def mock_devices_response(mock_shutter_device, mock_awning_device) -> Dict[str, Any]:
    """Mock devices API response."""
    return {
        "devices": [
            mock_shutter_device,
            mock_awning_device,
        ]
    }


@pytest.fixture
def mock_device_state_response() -> Dict[str, Any]:
    """Mock device state response."""
    return {
        "online": True,
        "openPercent": 75,
        "openState": ["OPEN"],
    }


@pytest.fixture
def mock_execute_response() -> Dict[str, Any]:
    """Mock device execute response."""
    return {
        "ids": ["shutter_001"],
        "status": "SUCCESS",
        "states": {
            "online": True,
            "openPercent": 100,
            "openState": ["OPEN"],
        },
    }


@pytest.fixture
def mock_error_response() -> Dict[str, Any]:
    """Mock API error response."""
    return {
        "error": "device_offline",
        "errorCode": "deviceOffline",
        "status": "ERROR",
    }


@pytest.fixture
def mock_everhome_api():
    """Mock the Everhome API."""
    from unittest.mock import AsyncMock

    mock_instance = AsyncMock()
    mock_instance.authenticate.return_value = True
    mock_instance.refresh_token.return_value = True
    mock_instance.get_devices.return_value = {"devices": []}
    mock_instance.get_device_state.return_value = {"online": True}
    mock_instance.execute_command.return_value = {"status": "SUCCESS"}
    mock_instance.close = AsyncMock(return_value=None)

    return mock_instance


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_everhome_api,
    mock_devices_response,
):
    """Set up the integration with mocked data."""
    # Configure mock API responses
    mock_everhome_api.authenticate.return_value = True
    mock_everhome_api.get_devices.return_value = mock_devices_response
    mock_everhome_api.close.return_value = None

    # Add config entry to hass
    mock_config_entry.add_to_hass(hass)

    # Patch the API class
    with (
        patch(
            "custom_components.everhome.coordinator.EverhomeAPI",
            return_value=mock_everhome_api,
        ),
        patch(
            "custom_components.everhome.api.EverhomeAPI", return_value=mock_everhome_api
        ),
    ):

        # Setup the integration
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify the entry was loaded
        assert result is True
        assert mock_config_entry.state == ConfigEntryState.LOADED

        yield mock_config_entry


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for API testing."""
    with patch("aiohttp.ClientSession") as mock_session:
        yield mock_session

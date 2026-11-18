"""Fixtures for Everhome integration tests.

Device payloads follow the documented `GET /device` schema
(https://everhome.cloud/en/developer/api): `id` is an int, state lives in
`states`, and there are no `position`/`capabilities`/`model` fields.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.everhome.const import API_BASE_URL, API_DEVICE_URL, DOMAIN

CLIENT_ID = "test_client_id"
CLIENT_SECRET = "test_client_secret"
DEVICE_URL = f"{API_BASE_URL}{API_DEVICE_URL}"
TOKEN_URL = f"{API_BASE_URL}/oauth2/token"


def execute_url(device_id: int) -> str:
    """Return the execute URL for a device."""
    return f"{API_BASE_URL}/device/{device_id}/execute"


def make_device(
    device_id: int,
    subtype: str,
    name: str,
    states: dict[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build a device in the documented API shape."""
    return {
        "id": device_id,
        "name": name,
        "subtype": subtype,
        "states": states or {},
        "actions": [],
        "disabled": False,
        "manufacturerid": 1,
        "productid": 1,
        "gatewayid": 1,
        "roomid": None,
        "homeid": 1,
        "statedefinitions": [],
        **extra,
    }


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


@pytest.fixture
def devices() -> list[dict[str, Any]]:
    """Return one device per supported platform plus unsupported/disabled ones."""
    return [
        make_device(8, "shutter", "Kinderzimmer", {"general": "up"}),
        make_device(9, "awning", "Terrasse", {"general": "in"}),
        make_device(10, "garagedoor", "Garage", {"general": "down"}),
        make_device(20, "light", "Flur", {"general": "on"}),
        make_device(30, "socket", "Steckdose", {"general": "off"}),
        make_device(40, "window", "Fenster", {"state": "closed"}),
        make_device(50, "speaker", "Unsupported speaker", {}),
        make_device(
            60, "shutter", "Disabled shutter", {"general": "up"}, disabled=True
        ),
    ]


@pytest.fixture
async def application_credentials(hass: HomeAssistant) -> None:
    """Register application credentials for the integration."""
    assert await async_setup_component(hass, "application_credentials", {})
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET), DOMAIN
    )


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Create a config entry with a valid (unexpired) token."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Everhome (6 devices)",
        entry_id="test_entry_id",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": time.time() + 3600,
            },
        },
    )


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    application_credentials: None,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
    devices: list[dict[str, Any]],
) -> MockConfigEntry:
    """Set up the integration with the device list from `devices`."""
    aioclient_mock.get(DEVICE_URL, json=devices)
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry

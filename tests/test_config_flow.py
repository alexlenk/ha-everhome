"""Test Everhome config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from aioresponses import aioresponses
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.everhome.config_flow import EverhomeFlowHandler
from custom_components.everhome.const import API_BASE_URL, DOMAIN


@pytest.fixture
def mock_oauth_impl():
    """Mock OAuth implementation."""
    impl_path = (
        "homeassistant.helpers.config_entry_oauth2_flow"
        ".async_get_config_entry_implementation"
    )
    with patch(impl_path) as mock_get_impl:
        mock_impl = AsyncMock()
        mock_impl.domain = DOMAIN
        mock_get_impl.return_value = mock_impl
        yield mock_impl


class TestEverhomeConfigFlow:
    """Test Everhome config flow."""

    def test_flow_handler_inheritance(self):
        """Test that flow handler inherits from correct base class."""
        from custom_components.everhome.config_flow import EverhomeFlowHandler
        from homeassistant.helpers.config_entry_oauth2_flow import AbstractOAuth2FlowHandler
        
        assert issubclass(EverhomeFlowHandler, AbstractOAuth2FlowHandler)
        assert hasattr(EverhomeFlowHandler, 'async_oauth_create_entry')

    async def test_oauth_create_entry_success(
        self,
        hass: HomeAssistant,
        mock_devices_response,
    ):
        """Test successful OAuth entry creation."""
        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "Everhome",
        }

        with aioresponses() as m:
            # Mock successful device fetch
            m.get(f"{API_BASE_URL}/device", payload=mock_devices_response["devices"])
            
            result = await flow.async_oauth_create_entry(oauth_data)
        
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Everhome (2 devices)"
        assert result["data"] == oauth_data

    async def test_oauth_create_entry_connection_error(
        self,
        hass: HomeAssistant,
    ):
        """Test OAuth entry creation with connection error."""
        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "invalid_token"},
            "name": "Everhome",
        }

        with aioresponses() as m:
            # Mock failed device fetch (401 unauthorized)
            m.get(f"{API_BASE_URL}/device", status=401)
            
            result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"

    async def test_oauth_create_entry_client_error(
        self,
        hass: HomeAssistant,
    ):
        """Test OAuth entry creation with aiohttp client error."""
        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "Everhome",
        }

        with aioresponses() as m:
            # Mock aiohttp client error
            m.get(f"{API_BASE_URL}/device", exception=aiohttp.ClientError("Network error"))
            
            result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"

    async def test_oauth_create_entry_unexpected_error(
        self,
        hass: HomeAssistant,
    ):
        """Test OAuth entry creation with unexpected error."""
        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "Everhome",
        }

        with aioresponses() as m:
            # Mock unexpected error
            m.get(f"{API_BASE_URL}/device", exception=Exception("Unexpected error"))
            
            result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "unknown"

    async def test_reauth_flow(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test the reauth flow."""
        mock_config_entry.add_to_hass(hass)

        flow = EverhomeFlowHandler()
        flow.hass = hass
        flow.context = {"source": config_entries.SOURCE_REAUTH}

        # Start reauth
        result = await flow.async_step_reauth(mock_config_entry.data)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

    async def test_reauth_confirm(
        self,
        hass: HomeAssistant,
        mock_oauth_impl,
    ):
        """Test reauth confirmation step."""
        flow = EverhomeFlowHandler()
        flow.hass = hass
        flow.context = {"source": config_entries.SOURCE_REAUTH}

        # Show reauth form
        result = await flow.async_step_reauth_confirm()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

        # Confirm reauth
        with patch.object(flow, "async_step_user") as mock_user_step:
            mock_user_step.return_value = {"type": FlowResultType.EXTERNAL_STEP}

            result = await flow.async_step_reauth_confirm({"confirm": True})

            mock_user_step.assert_called_once()

    async def test_oauth_create_entry_custom_name(
        self,
        hass: HomeAssistant,
        mock_devices_response,
    ):
        """Test OAuth entry creation with custom name."""
        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "My Smart Home",
        }

        with aioresponses() as m:
            # Mock successful device fetch
            m.get(f"{API_BASE_URL}/device", payload=mock_devices_response["devices"])
            
            result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "My Smart Home (2 devices)"
        assert result["data"] == oauth_data

    async def test_oauth_create_entry_no_name(
        self,
        hass: HomeAssistant,
        mock_devices_response,
    ):
        """Test OAuth entry creation without name."""
        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
        }

        with aioresponses() as m:
            # Mock successful device fetch
            m.get(f"{API_BASE_URL}/device", payload=mock_devices_response["devices"])
            
            result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Everhome (2 devices)"
        assert result["data"] == oauth_data

    def test_flow_handler_domain(self):
        """Test that flow handler has correct domain."""
        assert EverhomeFlowHandler.DOMAIN == DOMAIN

    def test_flow_handler_version(self):
        """Test that flow handler has correct version."""
        assert EverhomeFlowHandler.VERSION == 1

    def test_flow_handler_logger(self):
        """Test that flow handler logger is configured correctly."""
        flow = EverhomeFlowHandler()
        logger = flow.logger

        assert logger.name == "custom_components.everhome.config_flow"

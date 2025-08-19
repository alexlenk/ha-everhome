"""Test Everhome config flow."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.everhome.config_flow import EverhomeFlowHandler
from custom_components.everhome.const import DOMAIN


@pytest.fixture
def mock_oauth_impl():
    """Mock OAuth implementation."""
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_get_config_entry_implementation"
    ) as mock_get_impl:
        mock_impl = AsyncMock()
        mock_impl.domain = DOMAIN
        mock_get_impl.return_value = mock_impl
        yield mock_impl


@pytest.fixture
def mock_oauth_session():
    """Mock OAuth session."""
    with patch(
        "homeassistant.helpers.config_entry_oauth2_flow.async_create_auth_session"
    ) as mock_session:
        yield mock_session


class TestEverhomeConfigFlow:
    """Test Everhome config flow."""

    async def test_full_flow(
        self,
        hass: HomeAssistant,
        mock_oauth_impl,
        mock_oauth_session,
        mock_devices_response,
        mock_aiohttp_session,
    ):
        """Test the full OAuth flow."""
        # Mock successful device fetch
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_devices_response["devices"]

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_aiohttp_session.return_value = mock_session_instance

        # Start the flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.EXTERNAL_STEP
        assert result["step_id"] == "auth"

        # Mock OAuth completion
        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "Everhome",
        }

        with patch.object(
            hass.config_entries.flow, "async_configure"
        ) as mock_configure:
            mock_configure.return_value = (
                await hass.config_entries.flow._async_create_flow(
                    DOMAIN, context={"source": config_entries.SOURCE_USER}
                ).async_oauth_create_entry(oauth_data)
            )

            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], oauth_data
            )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Everhome (2 devices)"
        assert result["data"] == oauth_data

    async def test_oauth_create_entry_success(
        self,
        hass: HomeAssistant,
        mock_devices_response,
        mock_aiohttp_session,
    ):
        """Test successful OAuth entry creation."""
        # Mock successful device fetch
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_devices_response["devices"]

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_aiohttp_session.return_value = mock_session_instance

        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "Everhome",
        }

        result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Everhome (2 devices)"
        assert result["data"] == oauth_data

    async def test_oauth_create_entry_connection_error(
        self,
        hass: HomeAssistant,
        mock_aiohttp_session,
    ):
        """Test OAuth entry creation with connection error."""
        # Mock failed device fetch
        mock_response = AsyncMock()
        mock_response.status = 401

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_aiohttp_session.return_value = mock_session_instance

        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "invalid_token"},
            "name": "Everhome",
        }

        result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"

    async def test_oauth_create_entry_client_error(
        self,
        hass: HomeAssistant,
        mock_aiohttp_session,
    ):
        """Test OAuth entry creation with aiohttp client error."""
        # Mock aiohttp client error
        mock_session_instance = AsyncMock()
        mock_session_instance.get.side_effect = aiohttp.ClientError("Network error")
        mock_aiohttp_session.return_value = mock_session_instance

        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "Everhome",
        }

        result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"

    async def test_oauth_create_entry_unexpected_error(
        self,
        hass: HomeAssistant,
        mock_aiohttp_session,
    ):
        """Test OAuth entry creation with unexpected error."""
        # Mock unexpected error
        mock_session_instance = AsyncMock()
        mock_session_instance.get.side_effect = Exception("Unexpected error")
        mock_aiohttp_session.return_value = mock_session_instance

        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "Everhome",
        }

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
        mock_aiohttp_session,
    ):
        """Test OAuth entry creation with custom name."""
        # Mock successful device fetch
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_devices_response["devices"]

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_aiohttp_session.return_value = mock_session_instance

        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
            "name": "My Smart Home",
        }

        result = await flow.async_oauth_create_entry(oauth_data)

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "My Smart Home (2 devices)"
        assert result["data"] == oauth_data

    async def test_oauth_create_entry_no_name(
        self,
        hass: HomeAssistant,
        mock_devices_response,
        mock_aiohttp_session,
    ):
        """Test OAuth entry creation without name."""
        # Mock successful device fetch
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = mock_devices_response["devices"]

        mock_session_instance = AsyncMock()
        mock_session_instance.get.return_value.__aenter__.return_value = mock_response
        mock_aiohttp_session.return_value = mock_session_instance

        flow = EverhomeFlowHandler()
        flow.hass = hass

        oauth_data = {
            "token": {"access_token": "test_token"},
        }

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

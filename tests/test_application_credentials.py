"""Test Everhome application credentials."""

from __future__ import annotations

import pytest
from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant

from custom_components.everhome.application_credentials import (
    async_get_authorization_server,
)
from custom_components.everhome.const import API_BASE_URL


class TestEverhomeApplicationCredentials:
    """Test Everhome application credentials."""

    async def test_async_get_authorization_server(self, hass: HomeAssistant):
        """Test getting authorization server configuration."""
        auth_server = await async_get_authorization_server(hass)

        assert isinstance(auth_server, AuthorizationServer)
        assert auth_server.authorize_url == f"{API_BASE_URL}/oauth2/authorize"
        assert auth_server.token_url == f"{API_BASE_URL}/oauth2/token"

    async def test_authorization_server_urls(self, hass: HomeAssistant):
        """Test authorization server URLs are correctly constructed."""
        auth_server = await async_get_authorization_server(hass)

        expected_authorize_url = "https://everhome.cloud/oauth2/authorize"
        expected_token_url = "https://everhome.cloud/oauth2/token"

        assert auth_server.authorize_url == expected_authorize_url
        assert auth_server.token_url == expected_token_url

    async def test_authorization_server_consistency(self, hass: HomeAssistant):
        """Test that multiple calls return consistent configuration."""
        auth_server1 = await async_get_authorization_server(hass)
        auth_server2 = await async_get_authorization_server(hass)

        assert auth_server1.authorize_url == auth_server2.authorize_url
        assert auth_server1.token_url == auth_server2.token_url

    async def test_authorization_server_type(self, hass: HomeAssistant):
        """Test that function returns correct type."""
        auth_server = await async_get_authorization_server(hass)

        assert isinstance(auth_server, AuthorizationServer)
        assert hasattr(auth_server, "authorize_url")
        assert hasattr(auth_server, "token_url")

    async def test_authorization_server_immutable(self, hass: HomeAssistant):
        """Test that authorization server configuration is properly structured."""
        auth_server = await async_get_authorization_server(hass)

        # Verify the URLs are strings and not empty
        assert isinstance(auth_server.authorize_url, str)
        assert isinstance(auth_server.token_url, str)
        assert len(auth_server.authorize_url) > 0
        assert len(auth_server.token_url) > 0

        # Verify URLs contain expected components
        assert "oauth2" in auth_server.authorize_url
        assert "oauth2" in auth_server.token_url
        assert "authorize" in auth_server.authorize_url
        assert "token" in auth_server.token_url

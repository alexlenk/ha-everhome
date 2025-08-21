"""Test Everhome API authentication."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from custom_components.everhome.api import EverhomeAuth


class TestEverhomeAuth:
    """Test Everhome API authentication."""

    @pytest.fixture
    def mock_oauth_session(self):
        """Mock OAuth2Session."""
        session = AsyncMock(spec=config_entry_oauth2_flow.OAuth2Session)
        session.token = {"access_token": "test_access_token"}
        session.async_ensure_token_valid.return_value = None
        return session

    @pytest.fixture
    def everhome_auth(self, hass: HomeAssistant, mock_oauth_session):
        """Create EverhomeAuth fixture."""
        return EverhomeAuth(hass, mock_oauth_session)

    def test_initialization(self, hass: HomeAssistant, mock_oauth_session):
        """Test EverhomeAuth initialization."""
        auth = EverhomeAuth(hass, mock_oauth_session)

        assert auth.hass == hass
        assert auth.session == mock_oauth_session
        assert auth.aiohttp_session is not None

    async def test_async_get_access_token_success(
        self, everhome_auth, mock_oauth_session
    ):
        """Test successful access token retrieval."""
        token = await everhome_auth.async_get_access_token()

        assert token == "test_access_token"
        mock_oauth_session.async_ensure_token_valid.assert_called_once()

    async def test_async_get_access_token_refreshes_token(
        self, everhome_auth, mock_oauth_session
    ):
        """Test that get access token ensures token validity."""
        # Simulate token refresh
        mock_oauth_session.async_ensure_token_valid.return_value = None
        mock_oauth_session.token = {"access_token": "refreshed_access_token"}

        token = await everhome_auth.async_get_access_token()

        assert token == "refreshed_access_token"
        mock_oauth_session.async_ensure_token_valid.assert_called_once()

    async def test_async_get_access_token_multiple_calls(
        self, everhome_auth, mock_oauth_session
    ):
        """Test multiple calls to get access token."""
        # First call
        token1 = await everhome_auth.async_get_access_token()
        assert token1 == "test_access_token"

        # Second call
        token2 = await everhome_auth.async_get_access_token()
        assert token2 == "test_access_token"

        # Should call ensure_token_valid for each request
        assert mock_oauth_session.async_ensure_token_valid.call_count == 2

    async def test_async_get_access_token_handles_token_refresh_exception(
        self, everhome_auth, mock_oauth_session
    ):
        """Test handling of token refresh exceptions."""
        mock_oauth_session.async_ensure_token_valid.side_effect = Exception(
            "Token refresh failed"
        )

        with pytest.raises(Exception, match="Token refresh failed"):
            await everhome_auth.async_get_access_token()

    async def test_async_get_access_token_with_different_token_structure(
        self, hass: HomeAssistant, mock_aiohttp_session
    ):
        """Test access token retrieval with different token structures."""
        # Test with token containing additional fields
        mock_oauth_session = AsyncMock(spec=config_entry_oauth2_flow.OAuth2Session)
        mock_oauth_session.token = {
            "access_token": "complex_access_token",
            "refresh_token": "refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_oauth_session.async_ensure_token_valid.return_value = None

        auth = EverhomeAuth(hass, mock_oauth_session)
        token = await auth.async_get_access_token()

        assert token == "complex_access_token"

    async def test_async_get_access_token_empty_token(
        self, hass: HomeAssistant, mock_aiohttp_session
    ):
        """Test access token retrieval with empty token."""
        mock_oauth_session = AsyncMock(spec=config_entry_oauth2_flow.OAuth2Session)
        mock_oauth_session.token = {"access_token": ""}
        mock_oauth_session.async_ensure_token_valid.return_value = None

        auth = EverhomeAuth(hass, mock_oauth_session)
        token = await auth.async_get_access_token()

        assert token == ""

    async def test_async_get_access_token_none_token(
        self, hass: HomeAssistant, mock_aiohttp_session
    ):
        """Test access token retrieval with None token."""
        mock_oauth_session = AsyncMock(spec=config_entry_oauth2_flow.OAuth2Session)
        mock_oauth_session.token = {"access_token": None}
        mock_oauth_session.async_ensure_token_valid.return_value = None

        auth = EverhomeAuth(hass, mock_oauth_session)
        token = await auth.async_get_access_token()

        assert token is None

    def test_aiohttp_session_property(self, everhome_auth):
        """Test that aiohttp_session property returns correct session."""
        assert everhome_auth.aiohttp_session is not None

    async def test_token_validation_called_before_access(
        self, everhome_auth, mock_oauth_session
    ):
        """Test that token validation is always called before accessing token."""
        # Reset call count
        mock_oauth_session.async_ensure_token_valid.reset_mock()

        await everhome_auth.async_get_access_token()

        # Ensure token validation was called
        mock_oauth_session.async_ensure_token_valid.assert_called_once()

        # And that it was called before accessing the token
        assert mock_oauth_session.async_ensure_token_valid.called

    async def test_concurrent_token_requests(self, everhome_auth, mock_oauth_session):
        """Test concurrent access token requests."""
        import asyncio

        # Make multiple concurrent requests
        tasks = [everhome_auth.async_get_access_token() for _ in range(5)]

        results = await asyncio.gather(*tasks)

        # All should return the same token
        assert all(token == "test_access_token" for token in results)

        # Token validation should have been called for each request
        assert mock_oauth_session.async_ensure_token_valid.call_count == 5

    def test_auth_object_state_persistence(self, hass: HomeAssistant):
        """Test that EverhomeAuth maintains state correctly."""
        mock_oauth_session = AsyncMock(spec=config_entry_oauth2_flow.OAuth2Session)
        mock_oauth_session.token = {"access_token": "persistent_token"}

        auth = EverhomeAuth(hass, mock_oauth_session)

        # Verify initial state
        assert auth.hass == hass
        assert auth.session == mock_oauth_session
        assert auth.aiohttp_session is not None

        # State should persist
        assert auth.session.token["access_token"] == "persistent_token"

    async def test_token_refresh_side_effects(self, everhome_auth, mock_oauth_session):
        """Test side effects of token refresh."""
        # Simulate token change during refresh
        original_token = "original_token"
        refreshed_token = "refreshed_token"

        mock_oauth_session.token = {"access_token": original_token}

        def refresh_token():
            mock_oauth_session.token = {"access_token": refreshed_token}

        mock_oauth_session.async_ensure_token_valid.side_effect = refresh_token

        token = await everhome_auth.async_get_access_token()

        assert token == refreshed_token
        mock_oauth_session.async_ensure_token_valid.assert_called_once()

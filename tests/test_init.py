"""Test Everhome integration setup and unloading."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from custom_components.everhome import async_setup_entry, async_unload_entry
from custom_components.everhome.const import DOMAIN, PLATFORMS

# Constants for long import paths
OAUTH2_GET_IMPL = (
    "homeassistant.helpers.config_entry_oauth2_flow."
    "async_get_config_entry_implementation"
)
OAUTH2_SESSION = "homeassistant.helpers.config_entry_oauth2_flow.OAuth2Session"


class TestEverhomeInit:
    """Test Everhome integration initialization."""

    async def test_setup_entry_success(
        self,
        hass: HomeAssistant,
        mock_config_entry,
        mock_everhome_api,
        mock_devices_response,
    ):
        """Test successful setup of config entry."""
        mock_config_entry.add_to_hass(hass)

        # Mock OAuth components
        mock_implementation = AsyncMock()
        mock_session = AsyncMock()
        mock_auth = AsyncMock()
        mock_auth.async_get_access_token.return_value = "test_token"

        # Mock coordinator
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh.return_value = None

        with (
            patch(OAUTH2_GET_IMPL) as mock_get_impl,
            patch(OAUTH2_SESSION) as mock_oauth_session,
            patch("custom_components.everhome.EverhomeAuth") as mock_auth_class,
            patch(
                "custom_components.everhome.EverhomeDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch.object(
                hass.config_entries, "async_forward_entry_setups"
            ) as mock_forward_setups,
        ):

            mock_get_impl.return_value = mock_implementation
            mock_oauth_session.return_value = mock_session
            mock_auth_class.return_value = mock_auth
            mock_coordinator_class.return_value = mock_coordinator
            mock_forward_setups.return_value = True

            result = await async_setup_entry(hass, mock_config_entry)

            assert result is True
            assert DOMAIN in hass.data
            assert mock_config_entry.entry_id in hass.data[DOMAIN]
            assert hass.data[DOMAIN][mock_config_entry.entry_id] == mock_coordinator

            # Verify coordinator was set up
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()
            mock_forward_setups.assert_called_once_with(mock_config_entry, PLATFORMS)

    async def test_setup_entry_auth_failed(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test setup failure due to authentication error."""
        mock_config_entry.add_to_hass(hass)

        # Mock OAuth components
        mock_implementation = AsyncMock()
        mock_session = AsyncMock()
        mock_auth = AsyncMock()

        # Mock 401 authentication error
        auth_error = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=401,
            message="Unauthorized",
        )
        mock_auth.async_get_access_token.side_effect = auth_error

        with (
            patch(OAUTH2_GET_IMPL) as mock_get_impl,
            patch(OAUTH2_SESSION) as mock_oauth_session,
            patch("custom_components.everhome.EverhomeAuth") as mock_auth_class,
        ):

            mock_get_impl.return_value = mock_implementation
            mock_oauth_session.return_value = mock_session
            mock_auth_class.return_value = mock_auth

            with pytest.raises(ConfigEntryAuthFailed):
                await async_setup_entry(hass, mock_config_entry)

    async def test_setup_entry_not_ready_client_response_error(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test setup failure due to server error."""
        mock_config_entry.add_to_hass(hass)

        # Mock OAuth components
        mock_implementation = AsyncMock()
        mock_session = AsyncMock()
        mock_auth = AsyncMock()

        # Mock 500 server error
        server_error = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=500,
            message="Internal Server Error",
        )
        mock_auth.async_get_access_token.side_effect = server_error

        with (
            patch(OAUTH2_GET_IMPL) as mock_get_impl,
            patch(OAUTH2_SESSION) as mock_oauth_session,
            patch("custom_components.everhome.EverhomeAuth") as mock_auth_class,
        ):

            mock_get_impl.return_value = mock_implementation
            mock_oauth_session.return_value = mock_session
            mock_auth_class.return_value = mock_auth

            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, mock_config_entry)

    async def test_setup_entry_not_ready_client_error(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test setup failure due to client error."""
        mock_config_entry.add_to_hass(hass)

        # Mock OAuth components
        mock_implementation = AsyncMock()
        mock_session = AsyncMock()
        mock_auth = AsyncMock()

        # Mock client connection error
        client_error = aiohttp.ClientError("Connection failed")
        mock_auth.async_get_access_token.side_effect = client_error

        with (
            patch(OAUTH2_GET_IMPL) as mock_get_impl,
            patch(OAUTH2_SESSION) as mock_oauth_session,
            patch("custom_components.everhome.EverhomeAuth") as mock_auth_class,
        ):

            mock_get_impl.return_value = mock_implementation
            mock_oauth_session.return_value = mock_session
            mock_auth_class.return_value = mock_auth

            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, mock_config_entry)

    async def test_setup_entry_coordinator_refresh_failure(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test setup failure due to coordinator refresh error."""
        mock_config_entry.add_to_hass(hass)

        # Mock OAuth components
        mock_implementation = AsyncMock()
        mock_session = AsyncMock()
        mock_auth = AsyncMock()
        mock_auth.async_get_access_token.return_value = "test_token"

        # Mock coordinator that fails on first refresh
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh.side_effect = Exception(
            "Refresh failed"
        )

        with (
            patch(OAUTH2_GET_IMPL) as mock_get_impl,
            patch(OAUTH2_SESSION) as mock_oauth_session,
            patch("custom_components.everhome.EverhomeAuth") as mock_auth_class,
            patch(
                "custom_components.everhome.EverhomeDataUpdateCoordinator"
            ) as mock_coordinator_class,
        ):

            mock_get_impl.return_value = mock_implementation
            mock_oauth_session.return_value = mock_session
            mock_auth_class.return_value = mock_auth
            mock_coordinator_class.return_value = mock_coordinator

            with pytest.raises(Exception, match="Refresh failed"):
                await async_setup_entry(hass, mock_config_entry)

    async def test_unload_entry_success(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test successful unloading of config entry."""
        # Set up initial data
        hass.data.setdefault(DOMAIN, {})
        mock_coordinator = AsyncMock()
        hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

        with patch.object(
            hass.config_entries, "async_unload_platforms"
        ) as mock_unload_platforms:
            mock_unload_platforms.return_value = True

            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            assert mock_config_entry.entry_id not in hass.data[DOMAIN]
            mock_unload_platforms.assert_called_once_with(mock_config_entry, PLATFORMS)

    async def test_unload_entry_failure(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test failed unloading of config entry."""
        # Set up initial data
        hass.data.setdefault(DOMAIN, {})
        mock_coordinator = AsyncMock()
        hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

        with patch.object(
            hass.config_entries, "async_unload_platforms"
        ) as mock_unload_platforms:
            mock_unload_platforms.return_value = False

            result = await async_unload_entry(hass, mock_config_entry)

            assert result is False
            # Data should still be there on failed unload
            assert mock_config_entry.entry_id in hass.data[DOMAIN]
            mock_unload_platforms.assert_called_once_with(mock_config_entry, PLATFORMS)

    async def test_unload_entry_no_data(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test unloading when no data exists."""
        # Don't set up any data

        with patch.object(
            hass.config_entries, "async_unload_platforms"
        ) as mock_unload_platforms:
            mock_unload_platforms.return_value = True

            result = await async_unload_entry(hass, mock_config_entry)

            assert result is True
            # Should handle KeyError gracefully
            mock_unload_platforms.assert_called_once_with(mock_config_entry, PLATFORMS)

    async def test_setup_entry_data_structure(
        self,
        hass: HomeAssistant,
        mock_config_entry,
    ):
        """Test that setup creates proper data structure."""
        # Initially no DOMAIN data
        assert DOMAIN not in hass.data

        mock_config_entry.add_to_hass(hass)

        # Mock all dependencies
        mock_implementation = AsyncMock()
        mock_session = AsyncMock()
        mock_auth = AsyncMock()
        mock_auth.async_get_access_token.return_value = "test_token"
        mock_coordinator = AsyncMock()
        mock_coordinator.async_config_entry_first_refresh.return_value = None

        with (
            patch(OAUTH2_GET_IMPL) as mock_get_impl,
            patch(OAUTH2_SESSION) as mock_oauth_session,
            patch("custom_components.everhome.EverhomeAuth") as mock_auth_class,
            patch(
                "custom_components.everhome.EverhomeDataUpdateCoordinator"
            ) as mock_coordinator_class,
            patch.object(hass.config_entries, "async_forward_entry_setups"),
        ):

            mock_get_impl.return_value = mock_implementation
            mock_oauth_session.return_value = mock_session
            mock_auth_class.return_value = mock_auth
            mock_coordinator_class.return_value = mock_coordinator

            await async_setup_entry(hass, mock_config_entry)

            # Verify data structure
            assert DOMAIN in hass.data
            assert isinstance(hass.data[DOMAIN], dict)
            assert mock_config_entry.entry_id in hass.data[DOMAIN]

"""Config flow for Everhome integration."""

import logging
from typing import Any, Optional

import aiohttp
import voluptuous as vol
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class EverhomeFlowHandler(config_entry_oauth2_flow.AbstractOAuth2FlowHandler):
    """Config flow to handle Everhome OAuth2 authentication."""

    DOMAIN = DOMAIN
    VERSION = 1

    # Allow multiple config entries
    _async_get_entry_with_matching_unique_id = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> FlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create an entry for the OAuth2 config flow."""
        session = async_get_clientsession(self.hass)
        access_token = data["token"]["access_token"]

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get(f"{API_BASE_URL}/device", headers=headers) as resp:
                if resp.status != 200:
                    return self.async_abort(reason="cannot_connect")
                devices = await resp.json()

            # Use the name from the OAuth application for the config entry title
            # This allows users to distinguish between multiple accounts
            name = data.get("name", "Everhome")

            return self.async_create_entry(
                title=f"{name} ({len(devices)} devices)",
                data=data,
            )
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to the Everhome API: %s", err)
            return self.async_abort(reason="cannot_connect")
        except Exception as err:
            _LOGGER.exception("Unexpected error occurred: %s", err)
            return self.async_abort(reason="unknown")

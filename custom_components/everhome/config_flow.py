"""Config flow for Everhome integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

import voluptuous as vol
from aiohttp import ClientError
from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE_URL, API_DEVICE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(  # type: ignore[call-arg]
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Everhome OAuth2 authentication."""

    DOMAIN = DOMAIN
    VERSION = 1

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Validate the token, then create the entry (or update it on reauth)."""
        session = async_get_clientsession(self.hass)
        headers = {"Authorization": f"Bearer {data['token']['access_token']}"}

        try:
            async with session.get(
                f"{API_BASE_URL}{API_DEVICE_URL}", headers=headers
            ) as resp:
                if resp.status != HTTPStatus.OK:
                    _LOGGER.error(
                        "Everhome API returned %s while validating the token",
                        resp.status,
                    )
                    return self.async_abort(reason="cannot_connect")
                devices = await resp.json()
        except (ClientError, TimeoutError) as err:
            _LOGGER.error("Error connecting to the Everhome API: %s", err)
            return self.async_abort(reason="cannot_connect")
        except ValueError as err:
            _LOGGER.error("Invalid response from the Everhome API: %s", err)
            return self.async_abort(reason="unknown")

        if self.source == SOURCE_REAUTH:
            return self.async_update_reload_and_abort(
                self._get_reauth_entry(), data_updates=data
            )

        return self.async_create_entry(
            title=f"Everhome ({len(devices)} devices)",
            data=data,
        )

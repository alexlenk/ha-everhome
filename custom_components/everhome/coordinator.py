"""Data update coordinator for Everhome integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from http import HTTPStatus
from typing import Any

from aiohttp.client_exceptions import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    HomeAssistantError,
    OAuth2TokenRequestError,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EverhomeAuth
from .const import (
    API_BASE_URL,
    API_DEVICE_EXECUTE_URL,
    API_DEVICE_URL,
    DOMAIN,
    SUPPORTED_SUBTYPES,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type EverhomeConfigEntry = ConfigEntry[EverhomeDataUpdateCoordinator]


class EverhomeDataUpdateCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Class to manage fetching data from the API."""

    config_entry: EverhomeConfigEntry

    def __init__(
        self, hass: HomeAssistant, auth: EverhomeAuth, entry: EverhomeConfigEntry
    ) -> None:
        """Initialize."""
        self.auth = auth

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        """Update data via API."""
        try:
            return await self._get_devices()
        except OAuth2TokenRequestError:
            # Let the coordinator handle token refresh failures itself:
            # it starts reauth for non-recoverable ones.
            raise
        except (ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _get_devices(self) -> dict[int, dict[str, Any]]:
        """Get all supported, enabled devices from the API."""
        access_token = await self.auth.async_get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        async with self.auth.aiohttp_session.get(
            f"{API_BASE_URL}{API_DEVICE_URL}", headers=headers
        ) as resp:
            if resp.status == HTTPStatus.UNAUTHORIZED:
                raise ConfigEntryAuthFailed("Everhome rejected the access token")
            if resp.status != HTTPStatus.OK:
                _LOGGER.error("Failed to get devices: %s", await resp.text())
                raise UpdateFailed(f"Failed to get devices: {resp.status}")

            devices = await resp.json()

        return {
            device["id"]: device
            for device in devices
            if device.get("subtype") in SUPPORTED_SUBTYPES
            and not device.get("disabled", False)
        }

    async def execute_device_action(self, device_id: int, action: str) -> None:
        """Execute an action on a device.

        Raises HomeAssistantError if everHome does not accept the command, so the
        failure shows up in the service call / automation trace.
        """
        access_token = await self.auth.async_get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        url = f"{API_BASE_URL}{API_DEVICE_EXECUTE_URL.format(device_id=device_id)}"

        try:
            async with self.auth.aiohttp_session.post(
                url, headers=headers, json={"action": action}
            ) as resp:
                body = await resp.text()
                if resp.status >= HTTPStatus.BAD_REQUEST:
                    _LOGGER.error(
                        "Failed to execute action %s on device %s: %s %s",
                        action,
                        device_id,
                        resp.status,
                        body,
                    )
                    raise HomeAssistantError(
                        f"Everhome rejected action '{action}' for device "
                        f"{device_id} (HTTP {resp.status})"
                    )
                _LOGGER.debug(
                    "Executed action %s on device %s: %s %s",
                    action,
                    device_id,
                    resp.status,
                    body,
                )
        except (ClientError, TimeoutError) as err:
            _LOGGER.error(
                "Error executing action %s on device %s: %s",
                action,
                device_id,
                err,
            )
            raise HomeAssistantError(
                f"Error sending action '{action}' to device {device_id}: {err}"
            ) from err

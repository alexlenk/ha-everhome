"""Data update coordinator for Everhome integration."""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Optional

from aiohttp.client_exceptions import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class EverhomeDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self, hass: HomeAssistant, auth: EverhomeAuth, entry: ConfigEntry
    ) -> None:
        """Initialize."""
        self.auth = auth
        self.hass = hass
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via API."""
        try:
            # Get all devices
            return await self._get_devices()
        except (ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _get_devices(self) -> dict[str, Any]:
        """Get all devices from the API."""
        access_token = await self.auth.async_get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        async with self.auth.aiohttp_session.get(
            f"{API_BASE_URL}{API_DEVICE_URL}", headers=headers
        ) as resp:
            if resp.status != 200:
                _LOGGER.error("Failed to get devices: %s", await resp.text())
                raise UpdateFailed(f"Failed to get devices: {resp.status}")

            devices = await resp.json()

            # Filter for shutter-type devices
            shutter_devices = {}
            for device in devices:
                if device.get("subtype") in [
                    "shutter",
                    "blind",
                    "awning",
                    "curtain",
                    "garagedoor",
                ]:
                    shutter_devices[device["id"]] = device

            return shutter_devices

    async def execute_device_action(
        self,
        device_id: str,
        action: str,
        params: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Execute an action on a device."""
        access_token = await self.auth.async_get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        url = f"{API_BASE_URL}{API_DEVICE_EXECUTE_URL.format(device_id=device_id)}"
        data = {"action": action}
        if params:
            data.update(params)

        try:
            async with self.auth.aiohttp_session.post(
                url, headers=headers, json=data
            ) as resp:
                if resp.status >= 400:
                    _LOGGER.error(
                        "Failed to execute action %s on device %s: %s",
                        action,
                        device_id,
                        await resp.text(),
                    )
                    return False
                return True
        except (ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error(
                "Error executing action %s on device %s: %s",
                action,
                device_id,
                err,
            )
            return False

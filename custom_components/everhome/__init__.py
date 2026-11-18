"""The Everhome integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .api import EverhomeAuth
from .const import PLATFORMS
from .coordinator import EverhomeConfigEntry, EverhomeDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: EverhomeConfigEntry) -> bool:
    """Set up Everhome from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    coordinator = EverhomeDataUpdateCoordinator(
        hass, EverhomeAuth(hass, session), entry
    )

    # Token refresh failures raised here are already classified by Home
    # Assistant (OAuth2TokenRequestReauthError starts reauth, transient ones
    # retry setup), so no extra handling is needed.
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EverhomeConfigEntry) -> bool:
    """Unload a config entry."""
    return bool(await hass.config_entries.async_unload_platforms(entry, PLATFORMS))

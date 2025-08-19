"""API for Everhome bound to HASS OAuth."""

from typing import cast

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class EverhomeAuth:
    """Provide Everhome authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize Everhome Auth."""
        self.hass = hass
        self.session = oauth_session
        self.aiohttp_session = async_get_clientsession(hass)

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        await self.session.async_ensure_token_valid()
        return cast(str, self.session.token["access_token"])

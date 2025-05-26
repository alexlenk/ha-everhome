"""Application credentials platform for Everhome."""

from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant

from .const import API_BASE_URL


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return authorization server."""
    return AuthorizationServer(
        authorize_url=f"{API_BASE_URL}/oauth2/authorize",
        token_url=f"{API_BASE_URL}/oauth2/token",
    )
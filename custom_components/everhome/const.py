"""Constants for the Everhome integration."""

DOMAIN = "everhome"
PLATFORMS = ["cover"]

# Configuration
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_TOKEN_EXPIRY = "token_expiry"

# API endpoints
API_BASE_URL = "https://everhome.cloud"
API_TOKEN_URL = "/oauth2/token"
API_AUTHORIZE_URL = "/oauth2/authorize"
API_DEVICE_URL = "/device"
API_DEVICE_EXECUTE_URL = "/device/{device_id}/execute"

# Update interval in seconds (5 minutes)
UPDATE_INTERVAL = 300

# Shutter states
STATE_OPEN = "open"
STATE_CLOSED = "closed"
STATE_OPENING = "opening"
STATE_CLOSING = "closing"
STATE_STOPPED = "stopped"

# Shutter actions
ACTION_OPEN = "up"
ACTION_CLOSE = "down"
ACTION_STOP = "stop"

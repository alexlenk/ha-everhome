"""Constants for the Everhome integration."""

DOMAIN = "everhome"
PLATFORMS = ["cover", "binary_sensor", "light", "switch"]

# Device subtypes grouped by platform
COVER_SUBTYPES = {"shutter", "blind", "awning", "curtain", "garagedoor"}
BINARY_SENSOR_SUBTYPES = {
    "door",
    "window",
    "motiondetector",
    "smokedetector",
    "waterdetector",
}
LIGHT_SUBTYPES = {"light"}
SWITCH_SUBTYPES = {"socket", "watering"}
SUPPORTED_SUBTYPES = (
    COVER_SUBTYPES | BINARY_SENSOR_SUBTYPES | LIGHT_SUBTYPES | SWITCH_SUBTYPES
)

# API endpoints (https://everhome.cloud/en/developer/api)
API_BASE_URL = "https://everhome.cloud"
API_DEVICE_URL = "/device"
API_DEVICE_EXECUTE_URL = "/device/{device_id}/execute"

# Update interval in seconds (5 minutes)
UPDATE_INTERVAL = 300

# Documented values of states.general for covers.
# Shutters, blinds, curtains and garage doors report "up"/"down";
# awnings report "out" (extended = open) / "in" (retracted = closed).
COVER_OPEN_STATES = {"up", "out"}
COVER_CLOSED_STATES = {"down", "in"}

# Cover actions
ACTION_OPEN = "up"
ACTION_CLOSE = "down"
ACTION_STOP = "stop"

# On/off actions and states (lights, sockets, watering)
ACTION_ON = "on"
ACTION_OFF = "off"
STATE_ON = "on"
STATE_OFF = "off"

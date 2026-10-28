"""Constants for Room Comfort."""

from homeassistant.const import Platform

DOMAIN = "room_comfort"
VERSION = "0.3.0"
PLATFORMS = [Platform.CLIMATE, Platform.BUTTON, Platform.SWITCH, Platform.NUMBER]
DEFAULTS = {
    "name": "Room",
    "radiators": [],
    "air_conditioner": "",
    "windows": [],
    "tolerance": 0.3,
    "boost_minutes": 20,
    "ac_cooldown_seconds": 180,
    "sensor_timeout_minutes": 60,
    "control_method": "pid",
    "pid_kp": .3,
    "pid_ki": .006,
    "pid_kd": .1,
    "pid_deadband": .1,
    "pid_update_seconds": 120,
    "home_temperature": 21.0,
    "away_temperature": 19.0,
    "vacation_temperature": 17.0,
}

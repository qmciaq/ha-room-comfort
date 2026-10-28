"""Explicit opt-in to operating the assigned devices."""

from homeassistant.components.switch import SwitchEntity
from .entity import HouseholdEntity, RoomEntity


async def async_setup_entry(hass, entry, async_add_entities):
    if entry.data.get("kind") == "household":
        async_add_entities([HouseholdSwitch(entry.runtime_data, key) for key in ("vacation", "coming_home", "automatic_away")])
    else:
        async_add_entities([ControlSwitch(entry.runtime_data)])


class ControlSwitch(RoomEntity, SwitchEntity):
    _attr_name = "Control devices"
    _attr_icon = "mdi:thermostat-auto"

    def __init__(self, controller):
        super().__init__(controller, "control_devices")

    @property
    def is_on(self):
        return self.controller.enabled

    async def async_turn_on(self, **kwargs):
        await self.controller.async_change(enabled=True)

    async def async_turn_off(self, **kwargs):
        await self.controller.async_change(enabled=False, cancel_boost=True)


class HouseholdSwitch(HouseholdEntity, SwitchEntity):
    def __init__(self, controller, key):
        super().__init__(controller, key)
        self.key = key
        self._attr_name = {"vacation": "Vacation", "coming_home": "Coming home comfort", "automatic_away": "Automatic away"}[key]
        self._attr_icon = {"vacation": "mdi:bag-suitcase", "coming_home": "mdi:home-clock", "automatic_away": "mdi:map-marker-account"}[key]

    @property
    def is_on(self):
        return self.controller.prewarming if self.key == "coming_home" else getattr(self.controller, self.key)

    async def async_turn_on(self, **kwargs):
        await self.controller.async_change(self.key, True)

    async def async_turn_off(self, **kwargs):
        await self.controller.async_change(self.key, False)


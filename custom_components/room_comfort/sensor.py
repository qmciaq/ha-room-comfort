"""Shared home-mode status and presence diagnostics."""

from homeassistant.components.sensor import SensorEntity
from .entity import HouseholdEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([HouseholdMode(entry.runtime_data)])


class HouseholdMode(HouseholdEntity, SensorEntity):
    _attr_name = "Home mode"
    _attr_icon = "mdi:home-thermometer"

    def __init__(self, controller):
        super().__init__(controller, "mode")

    @property
    def native_value(self):
        return self.controller.profile

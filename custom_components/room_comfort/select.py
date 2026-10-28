"""Select how each room prepares for a manual coming-home request."""

from homeassistant.components.select import SelectEntity
from .entity import RoomEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ComingHomeMode(entry.runtime_data)])


class ComingHomeMode(RoomEntity, SelectEntity):
    _attr_name = "Coming home mode"
    _attr_icon = "mdi:home-thermometer-outline"

    def __init__(self, controller):
        super().__init__(controller, "coming_home_mode")
        self._attr_options = ["heat", "cool"] if controller.ac else ["heat"]

    @property
    def current_option(self):
        return self.controller.coming_home_mode

    async def async_select_option(self, option):
        await self.controller.async_set_coming_home_mode(option)

"""Start or cancel a room boost."""

from homeassistant.components.button import ButtonEntity
from .entity import RoomEntity


async def async_setup_entry(hass, entry, async_add_entities):
    if entry.runtime_data.ac:
        async_add_entities([BoostButton(entry.runtime_data, False), BoostButton(entry.runtime_data, True)])


class BoostButton(RoomEntity, ButtonEntity):
    def __init__(self, controller, cancel):
        super().__init__(controller, "cancel_boost" if cancel else "heat_boost")
        self.cancel = cancel
        self._attr_name = "Cancel boost" if cancel else "Heat boost"
        self._attr_icon = "mdi:stop-circle-outline" if cancel else "mdi:fire"

    async def async_press(self):
        if self.cancel:
            await self.controller.async_change(cancel_boost=True)
        else:
            await self.controller.async_boost()

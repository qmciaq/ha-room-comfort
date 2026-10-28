"""Editable room targets exposed as ordinary HA number entities."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from .entity import RoomEntity


async def async_setup_entry(hass, entry, async_add_entities):
    c = entry.runtime_data
    async_add_entities([ProfileTemperature(c, profile, mode) for mode in (["heat", "cool"] if c.ac else ["heat"])
                        for profile in ("home", "away", "vacation")])


class ProfileTemperature(RoomEntity, NumberEntity):
    _attr_native_min_value = 5
    _attr_native_max_value = 30
    _attr_native_step = .5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer"

    def __init__(self, controller, profile, mode="heat"):
        super().__init__(controller, f"{profile}_cool_temperature" if mode == "cool" else f"{profile}_temperature")
        self.profile = profile
        self.hvac_mode = mode
        self._attr_name = f"{profile.title()} {'cooling' if mode == 'cool' else 'heating'} temperature"

    @property
    def native_value(self):
        return (self.controller.cool_targets if self.hvac_mode == "cool" else self.controller.targets)[self.profile]

    async def async_set_native_value(self, value):
        await self.controller.async_set_profile_temperature(self.profile, value, self.hvac_mode)


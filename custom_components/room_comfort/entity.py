"""Common room entity metadata."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class RoomEntity(Entity):
    """An entity belonging to a virtual room device."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, controller, key):
        self.controller = controller
        self._room_key = key
        self._attr_unique_id = f"{controller.entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, controller.entry.entry_id)},
            name=controller.config["name"],
            manufacturer="Room Comfort",
            model="Room thermostat",
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.controller.entity_ids[self._room_key] = self.entity_id
        self.async_on_remove(self.controller.async_subscribe(self.async_write_ha_state))


class HouseholdEntity(Entity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, controller, key):
        self.controller = controller
        self._home_key = key
        self._attr_unique_id = f"household_{key}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, "household")},
            name="Home comfort modes", manufacturer="Room Comfort", model="Household controller")

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.controller.entity_ids[self._home_key] = self.entity_id
        self.async_on_remove(self.controller.async_subscribe(self.async_write_ha_state))

    @property
    def extra_state_attributes(self):
        c = self.controller
        return {"room_comfort_household": True, "home_profile": c.profile,
                "presence_entities": c.config["presence_entities"], "home_zone": c.config["home_zone"],
                "memberships": c.memberships, "prewarm_ends_at": c.prewarm_until,
                "prewarm_ready": c.prewarm_ready, "household_entities": dict(c.entity_ids),
                "away_delay_minutes": c.config["away_delay_minutes"],
                "outdoor_settings": {key: value for key, value in c.config.items() if key.startswith("outdoor_")}}


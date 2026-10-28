"""The room-level thermostat."""

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError

from .entity import RoomEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([RoomThermostat(entry.runtime_data)])


class RoomThermostat(RoomEntity, ClimateEntity):
    """One target temperature; ordinary radiators or a timed AC assist."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 5
    _attr_max_temp = 30
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, controller):
        super().__init__(controller, "thermostat")

    @property
    def hvac_modes(self):
        return [HVACMode.OFF, HVACMode.HEAT, *([HVACMode.COOL] if self.controller.ac else [])]

    @property
    def hvac_mode(self):
        return HVACMode(self.controller.mode)

    @property
    def current_temperature(self):
        return self.controller.temperature

    @property
    def native_current_temperature(self):
        return self.controller.temperature

    @property
    def target_temperature(self):
        return self.controller.target

    @property
    def native_target_temperature(self):
        return self.controller.target

    @property
    def hvac_action(self):
        if not self.controller.enabled or self.controller.mode == "off":
            return HVACAction.OFF
        if self.controller.status in ("heating", "boosting"):
            return HVACAction.HEATING
        if self.controller.status == "cooling":
            return HVACAction.COOLING
        return HVACAction.IDLE

    @property
    def preset_modes(self):
        return ["radiators", *(["boost"] if self.controller.ac else [])]

    @property
    def preset_mode(self):
        return "boost" if self.controller.boost_until is not None else "radiators"

    @property
    def extra_state_attributes(self):
        c = self.controller
        return {
            "room_comfort": True,
            "room_name": c.config["name"],
            "config_entry_id": c.entry.entry_id,
            "control_switch": c.entity_ids.get("control_devices"),
            "boost_button": c.entity_ids.get("heat_boost"),
            "cancel_boost_button": c.entity_ids.get("cancel_boost"),
            "controller_status": c.status,
            "demand_status": c.demand.status,
            "control_devices": c.enabled,
            "room_sensor": c.config["temperature_sensor"],
            "radiators": c.radiators,
            "air_conditioner": c.ac or None,
            "windows": c.config["windows"],
            "boost_duration_minutes": c.config["boost_minutes"],
            "boost_ends_at": c.boost_until,
            "boost_remaining_seconds": max(0, int(c.boost_until - c.now())) if c.boost_until else 0,
            "desired_radiator_heat": c.demand.radiator_heat,
            "desired_ac_mode": c.demand.ac_mode,
            "device_errors": dict(c.errors),
            "control_method": c.config["control_method"],
            "heat_demand_percent": round(c.heat_output * 100, 1),
            "home_profile": c.profile,
            "profile_temperatures": dict(c.targets),
            "profile_temperature_unit": "°C",
            "profile_temperature_entities": {key: c.entity_ids.get(f"{key}_temperature") for key in c.targets},
            "household_entities": dict(c.household.entity_ids) if c.household else {},
        }

    async def async_set_hvac_mode(self, hvac_mode):
        mode = str(hvac_mode)
        if mode not in [str(m) for m in self.hvac_modes]:
            raise HomeAssistantError("Unsupported room HVAC mode")
        await self.controller.async_change(mode=mode, cancel_boost=True)

    async def async_set_temperature(self, **kwargs):
        target = kwargs.get(ATTR_TEMPERATURE, self.controller.target)
        mode = kwargs.get("hvac_mode", self.controller.mode)
        if str(mode) not in [str(m) for m in self.hvac_modes]:
            raise HomeAssistantError("Unsupported room HVAC mode")
        await self.controller.async_change(target=target, mode=str(mode),
                                           cancel_boost=str(mode) != "heat")

    async def async_set_preset_mode(self, preset_mode):
        if preset_mode == "boost" and self.controller.ac:
            await self.controller.async_boost()
        elif preset_mode == "radiators":
            await self.controller.async_change(mode="heat", cancel_boost=True)
        else:
            raise HomeAssistantError("Unsupported room preset")

    async def async_turn_on(self):
        await self.controller.async_change(mode="heat", cancel_boost=True)

    async def async_turn_off(self):
        await self.controller.async_change(mode="off", cancel_boost=True)

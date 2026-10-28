"""UI setup and options for a room, including capability and overlap checks."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector

from .const import DEFAULTS, DOMAIN
from .household import HOUSE_DEFAULTS


def room_schema(values):
    values = {**DEFAULTS, **values}
    fields = {
        vol.Required("name", default=values["name"]): str,
        vol.Required("temperature_sensor", default=values.get("temperature_sensor", vol.UNDEFINED)):
            selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="temperature")),
        vol.Required("radiators", default=values["radiators"]):
            selector.EntitySelector(selector.EntitySelectorConfig(domain="climate", multiple=True)),
        vol.Optional("air_conditioner", description={"suggested_value": values["air_conditioner"]}):
            selector.EntitySelector(selector.EntitySelectorConfig(domain="climate")),
        vol.Optional("windows", default=values["windows"]):
            selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)),
        vol.Required("tolerance", default=values["tolerance"]): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.5)),
        vol.Required("boost_minutes", default=values["boost_minutes"]): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
        vol.Required("ac_cooldown_seconds", default=values["ac_cooldown_seconds"]): vol.All(vol.Coerce(int), vol.Range(min=180, max=900)),
        vol.Required("sensor_timeout_minutes", default=values["sensor_timeout_minutes"]): vol.All(vol.Coerce(int), vol.Range(min=5, max=1440)),
        vol.Required("control_method", default=values["control_method"]): selector.SelectSelector(selector.SelectSelectorConfig(options=["pid", "hysteresis"])),
        vol.Required("home_temperature", default=values["home_temperature"]): vol.All(vol.Coerce(float), vol.Range(min=5, max=30)),
        vol.Required("away_temperature", default=values["away_temperature"]): vol.All(vol.Coerce(float), vol.Range(min=5, max=30)),
        vol.Required("vacation_temperature", default=values["vacation_temperature"]): vol.All(vol.Coerce(float), vol.Range(min=5, max=30)),
        vol.Required("pid_kp", default=values["pid_kp"]): vol.All(vol.Coerce(float), vol.Range(min=0, max=5)),
        vol.Required("pid_ki", default=values["pid_ki"]): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
        vol.Required("pid_kd", default=values["pid_kd"]): vol.All(vol.Coerce(float), vol.Range(min=0, max=5)),
        vol.Required("pid_deadband", default=values["pid_deadband"]): vol.All(vol.Coerce(float), vol.Range(min=.05, max=.5)),
        vol.Required("pid_update_seconds", default=values["pid_update_seconds"]): vol.All(vol.Coerce(int), vol.Range(min=60, max=900)),
    }
    return vol.Schema(fields)


def validate_room(hass, data, entry_id=None):
    if not data.get("name", "").strip() or not data.get("radiators"):
        return "room_required"
    devices = list(data["radiators"])
    ac = data.get("air_conditioner", "")
    if ac:
        devices.append(ac)
    if len(set(devices)) != len(devices):
        return "duplicate_device"
    registry = er.async_get(hass)
    for entity_id in devices:
        registered = registry.async_get(entity_id)
        if registered and registered.platform == DOMAIN:
            return "nested_room"
        state = hass.states.get(entity_id)
        modes = state.attributes.get("hvac_modes", []) if state else []
        required = {"off", "heat", "cool"} if entity_id == ac else {"off", "heat"}
        features = state.attributes.get("supported_features", 0) if state else 0
        if not required.issubset(modes) or not features & 1:
            return "unsupported_device"
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.entry_id == entry_id:
            continue
        existing = {**entry.data, **entry.options}
        assigned = {*existing.get("radiators", []), existing.get("air_conditioner", "")}
        if assigned.intersection(devices):
            return "already_assigned"
    sensor = hass.states.get(data["temperature_sensor"])
    if sensor is None or sensor.attributes.get("unit_of_measurement") not in ("°C", "°F"):
        return "invalid_sensor"
    return None


class RoomComfortConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_import(self, user_input):
        await self.async_set_unique_id("household")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Home modes", data={"kind": "household", **HOUSE_DEFAULTS})

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            user_input = {**DEFAULTS, **user_input}
            if error := validate_room(self.hass, user_input):
                errors["base"] = error
            else:
                return self.async_create_entry(title=user_input["name"], data=user_input)
        return self.async_show_form(step_id="user", data_schema=room_schema(user_input or {}), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return HouseholdOptionsFlow() if config_entry.data.get("kind") == "household" else RoomComfortOptionsFlow()


class RoomComfortOptionsFlow(config_entries.OptionsFlowWithReload):
    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            user_input = {**DEFAULTS, **user_input}
            if error := validate_room(self.hass, user_input, self.config_entry.entry_id):
                errors["base"] = error
            else:
                controller = self.config_entry.runtime_data
                for profile in ("home", "away", "vacation"):
                    await controller.async_set_profile_temperature(profile, user_input[f"{profile}_temperature"])
                self.hass.config_entries.async_update_entry(self.config_entry, title=user_input["name"])
                return self.async_create_entry(title="", data=user_input)
        values = user_input if user_input is not None else {**self.config_entry.data, **self.config_entry.options}
        if user_input is None and self.config_entry.runtime_data:
            values.update({f"{profile}_temperature": value for profile, value in self.config_entry.runtime_data.targets.items()})
        return self.async_show_form(step_id="init", data_schema=room_schema(values), errors=errors)


class HouseholdOptionsFlow(config_entries.OptionsFlowWithReload):
    async def async_step_household(self, user_input=None):
        return await self.async_step_init(user_input)

    async def async_step_init(self, user_input=None):
        values = {**HOUSE_DEFAULTS, **self.config_entry.data, **self.config_entry.options}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        schema = vol.Schema({
            vol.Required("presence_entities", default=values["presence_entities"]): selector.EntitySelector(selector.EntitySelectorConfig(domain=["person", "device_tracker"], multiple=True)),
            vol.Required("home_zone", default=values["home_zone"]): selector.EntitySelector(selector.EntitySelectorConfig(domain="zone")),
            vol.Required("away_delay_minutes", default=values["away_delay_minutes"]): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
            vol.Required("prewarm_hours", default=values["prewarm_hours"]): vol.All(vol.Coerce(float), vol.Range(min=.5, max=24)),
        })
        return self.async_show_form(step_id="household", data_schema=schema,
            description_placeholders={"purpose": "Home modes: all trackers must be outside the selected zone. Unknown states keep Home comfort. Vacation is manual; prewarm ends on arrival, cancellation or timeout."})

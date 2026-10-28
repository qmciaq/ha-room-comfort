"""Room lifecycle, state persistence, and interlocked device commands."""

import asyncio
from datetime import timedelta
import logging
from math import isfinite
import time

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfTemperature
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util.unit_conversion import TemperatureConverter

from .const import DEFAULTS, DOMAIN
from .engine import Demand, calculate_demand
from .pid import RoomPID, trv_target

_LOGGER = logging.getLogger(__name__)
BAD_STATES = {STATE_UNAVAILABLE, STATE_UNKNOWN}


class RoomController:
    def __init__(self, hass, entry, household=None):
        self.hass = hass
        self.entry = entry
        self.config = {**DEFAULTS, **entry.data, **entry.options}
        self.radiators = list(self.config["radiators"])
        self.ac = self.config["air_conditioner"]
        self.devices = [*self.radiators, *([self.ac] if self.ac else [])]
        self.mode = "off"
        self.targets = {key: self.config[f"{key}_temperature"] for key in ("home", "away", "vacation")}
        self.cool_targets = {key: self.config[f"{key}_cool_temperature"] for key in ("home", "away", "vacation")}
        self.coming_home_mode = self.config["coming_home_mode"] if self.ac else "heat"
        self.household = household
        self.pid = RoomPID(self.config["pid_kp"], self.config["pid_ki"], self.config["pid_kd"], self.config["pid_deadband"])
        self.heat_output = 0.0
        self._pid_active = False
        self._profile = self.profile
        self._pid_last_sent = {}
        if household:
            household.rooms.add(self)
        self.enabled = False
        self.boost_until = None
        self.demand = Demand()
        self.status = "observe_only"
        self.errors = {}
        self.entity_ids = {}
        self._listeners = set()
        self._unsubscribers = []
        self._lock = asyncio.Lock()
        self._pending = None
        self._stopped = False
        self._shutdown_pending = False
        self._last_ac_mode = "off"
        self._ac_off_since = self.now()
        self._last_command = {}
        self._store = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}")

    @staticmethod
    def now():
        return time.time()

    @property
    def profile(self):
        return self.household.profile if self.household else "home"

    @property
    def target_profile(self):
        return "home" if self.profile == "prewarming" else self.profile

    @property
    def target(self):
        return self.active_targets[self.target_profile]

    @target.setter
    def target(self, value):
        self.active_targets[self.target_profile] = value

    @property
    def active_targets(self):
        return self.cool_targets if self.mode == "cool" else self.targets

    @property
    def coming_home_target(self):
        targets = self.cool_targets if self.coming_home_mode == "cool" else self.targets
        return targets["home"]

    @property
    def coming_home_ready(self):
        if self.temperature is None:
            return False
        return (self.temperature <= self.coming_home_target + .2 if self.coming_home_mode == "cool"
                else self.temperature >= self.coming_home_target - .2)

    async def async_load(self):
        if saved := await self._store.async_load():
            mode = saved.get("mode", "off")
            self.mode = mode if mode in ("off", "heat", "cool") else "off"
            if self.mode == "cool" and not self.ac:
                self.mode = "off"
            try:
                value = float(saved.get("target", 21))
                self.targets["home"] = value if isfinite(value) and 5 <= value <= 30 else self.config["home_temperature"]
            except (TypeError, ValueError):
                self.targets["home"] = self.config["home_temperature"]
            for profile, value in saved.get("targets", {}).items():
                if profile in self.targets and isinstance(value, (int, float)) and isfinite(value) and 5 <= value <= 30:
                    self.targets[profile] = float(value)
            self.enabled = bool(saved.get("enabled", False))
            for profile, value in saved.get("cool_targets", {}).items():
                if profile in self.cool_targets and isinstance(value, (int, float)) and isfinite(value) and 5 <= value <= 30:
                    self.cool_targets[profile] = float(value)
            saved_mode = saved.get("coming_home_mode", self.coming_home_mode)
            if saved_mode in ("heat", "cool"):
                self.coming_home_mode = saved_mode if self.ac else "heat"
            self._shutdown_pending = bool(saved.get("shutdown_pending", False))
        # A boost is deliberately never resumed after a restart.
        if self.ac:
            state = self._state(self.ac)
            self._last_ac_mode = state.state if state else "off"

    def _stored_settings(self):
        return {"mode": self.mode, "target": self.targets["home"], "targets": dict(self.targets), "enabled": self.enabled,
                "shutdown_pending": self._shutdown_pending, "cool_targets": dict(self.cool_targets),
                "coming_home_mode": self.coming_home_mode}

    def _save(self):
        self._store.async_delay_save(self._stored_settings, 1)

    @property
    def temperature(self):
        state = self._state(self.config["temperature_sensor"])
        if not state:
            return None
        reported = getattr(state, "last_reported", state.last_updated)
        age = self.now() - reported.timestamp()
        if age > self.config["sensor_timeout_minutes"] * 60:
            return None
        try:
            value = float(state.state)
            unit = state.attributes.get("unit_of_measurement")
            if unit not in (UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT):
                return None
            value = TemperatureConverter.convert(value, unit, UnitOfTemperature.CELSIUS)
            return value if isfinite(value) and -30 <= value <= 60 else None
        except (TypeError, ValueError):
            return None

    def _state(self, entity_id):
        state = self.hass.states.get(entity_id)
        return state if state and state.state not in BAD_STATES else None

    @callback
    def async_subscribe(self, listener):
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    @callback
    def _publish(self):
        for listener in tuple(self._listeners):
            listener()

    @callback
    def async_start(self):
        watched = [self.config["temperature_sensor"], *self.devices, *self.config["windows"]]
        self._unsubscribers = [
            async_track_state_change_event(self.hass, watched, self._schedule),
            async_track_time_interval(self.hass, self._schedule, timedelta(seconds=15)),
        ]
        if self.household:
            self._unsubscribers.append(self.household.async_subscribe(self._schedule))
        self._schedule()

    @callback
    def _schedule(self, event=None):
        if not self._stopped and (self._pending is None or self._pending.done()):
            self._pending = self.entry.async_create_background_task(
                self.hass, self._scheduled_evaluate(), f"{DOMAIN} {self.entry.entry_id}"
            )

    async def _scheduled_evaluate(self):
        # Collapse state notifications caused by our own service calls.
        await asyncio.sleep(0.2)
        await self.async_evaluate()

    async def async_stop(self):
        self._stopped = True
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        if self._pending and not self._pending.done():
            self._pending.cancel()
            try:
                await self._pending
            except asyncio.CancelledError:
                pass
        async with self._lock:
            if self.enabled or self._shutdown_pending:
                for entity_id in self.devices:
                    await self._ensure_off(entity_id)
            # A settings reload can happen within the delayed-save interval.
            # Flush first so the replacement controller restores the latest target.
            await self._store.async_save(self._stored_settings())
        if self.household:
            self.household.rooms.discard(self)

    async def async_set_profile_temperature(self, profile, value, mode="heat"):
        async with self._lock:
            value = float(value)
            if profile not in self.targets or not isfinite(value) or not 5 <= value <= 30:
                raise HomeAssistantError("Profile target must be between 5 and 30 degrees Celsius")
            if mode not in ("heat", "cool") or (mode == "cool" and not self.ac):
                raise HomeAssistantError("Cooling requires an assigned air conditioner")
            (self.cool_targets if mode == "cool" else self.targets)[profile] = value
            self.pid.reset()
            self._save()
            await self._evaluate_locked()

    async def async_set_coming_home_mode(self, mode):
        async with self._lock:
            if mode not in ("heat", "cool") or (mode == "cool" and not self.ac):
                raise HomeAssistantError("Unsupported coming-home mode")
            self.coming_home_mode = mode
            self._save()
            await self._evaluate_locked()

    async def async_change(self, *, mode=None, target=None, enabled=None, cancel_boost=False):
        async with self._lock:
            if mode is not None and mode not in ("off", "heat", "cool"):
                raise HomeAssistantError("Unsupported room HVAC mode")
            if mode == "cool" and not self.ac:
                raise HomeAssistantError("This room has no air conditioner")
            if target is not None:
                value = float(target)
                if not isfinite(value) or not 5 <= value <= 30:
                    raise HomeAssistantError("Room target must be between 5 and 30 degrees Celsius")
            if mode is not None:
                if self.mode != mode:
                    self.demand = Demand()
                    self.pid.reset()
                self.mode = mode
            if target is not None:
                self.target = value
                self.pid.reset()
            if cancel_boost:
                self.boost_until = None
            was_enabled = self.enabled
            if enabled is not None:
                self.enabled = enabled
                if enabled:
                    self._shutdown_pending = False
            if was_enabled and not self.enabled:
                self._shutdown_pending = True
            self._save()
            await self._evaluate_locked()

    async def async_boost(self):
        async with self._lock:
            if not self.ac or not self._state(self.ac):
                raise HomeAssistantError("The room air conditioner is unavailable")
            if self.temperature is None:
                raise HomeAssistantError("The room temperature sensor is unavailable or stale")
            self.mode = "heat"
            self.boost_until = self.now() + self.config["boost_minutes"] * 60
            self._save()
            await self._evaluate_locked()

    async def async_evaluate(self):
        async with self._lock:
            if not self._stopped:
                await self._evaluate_locked()

    async def _evaluate_locked(self):
        self.errors = {}
        if self._profile != self.profile:
            self._profile = self.profile
            self.pid.reset()
            self.boost_until = None
        if self.profile == "prewarming" and self.enabled and self.mode != self.coming_home_mode:
            self.mode = self.coming_home_mode
            self.demand = Demand()
            self.pid.reset()
            self._save()
        if self.ac and (state := self._state(self.ac)):
            if state.state == "off" and self._last_ac_mode != "off":
                self._ac_off_since = self.now()
            self._last_ac_mode = state.state
        window_open = any(
            (state := self._state(entity_id)) is None or state.state != "off"
            for entity_id in self.config["windows"]
        )
        self.demand = calculate_demand(
            mode=self.mode, temperature=self.temperature, target=self.target,
            tolerance=self.config["tolerance"], previous=self.demand,
            boost_until=self.boost_until, now=self.now(), window_open=window_open,
        )
        if self.demand.boost_finished:
            self.boost_until = None
        self._pid_active = (self.config["control_method"] == "pid" and self.mode == "heat"
                            and self.temperature is not None and not window_open)
        if self._pid_active:
            self.heat_output = self.pid.update(self.temperature, self.target, self.now())
            self.demand = Demand(radiator_heat=self.heat_output > .03, ac_mode=self.demand.ac_mode,
                status="boosting" if self.demand.ac_mode == "heat" else "heating" if self.heat_output > .03 else "idle",
                boost_finished=self.demand.boost_finished)
        else:
            self.pid.reset()
            self.heat_output = 1.0 if self.demand.radiator_heat else 0.0
        if self.enabled:
            self.status = self.demand.status
            await self._apply()
        else:
            if self._shutdown_pending:
                for entity_id in self.devices:
                    await self._ensure_off(entity_id)
                if self._all_off(self.devices):
                    self._shutdown_pending = False
                    self._save()
                self.status = "stopping_devices" if self._shutdown_pending else "observe_only"
            else:
                self.status = "observe_only"
        self._publish()

    async def _call(self, entity_id, service, data):
        """Send at most one identical command per 30 seconds while awaiting feedback."""
        key = (entity_id, service, tuple(sorted(data.items())))
        if self.now() - self._last_command.get(key, float("-inf")) < 30:
            return False
        self._last_command[key] = self.now()
        try:
            async with asyncio.timeout(10):
                await self.hass.services.async_call(
                    "climate", service, {"entity_id": entity_id, **data}, blocking=True
                )
            return True
        except (HomeAssistantError, TimeoutError) as error:
            self.errors[entity_id] = str(error)
            _LOGGER.warning("Room %s: %s failed for %s: %s", self.config["name"], service, entity_id, error)
            return False

    async def _ensure_off(self, entity_id):
        state = self._state(entity_id)
        if state is None:
            self.errors[entity_id] = "unavailable: off cannot be confirmed"
            return False
        if state.state != "off":
            await self._call(entity_id, "set_hvac_mode", {"hvac_mode": "off"})
        state = self._state(entity_id)
        confirmed = state is not None and state.state == "off"
        if confirmed and entity_id == self.ac and self._last_ac_mode != "off":
            self._ac_off_since = self.now()
            self._last_ac_mode = "off"
        return confirmed

    def _all_off(self, entity_ids):
        return all((state := self._state(eid)) is not None and state.state == "off" for eid in entity_ids)

    async def _apply(self):
        desired = {entity_id: "heat" if self._pid_active or self.demand.radiator_heat else "off" for entity_id in self.radiators}
        if self.ac:
            desired[self.ac] = self.demand.ac_mode
        # Stop all unwanted or incompatible modes before sending any start command.
        for entity_id, mode in desired.items():
            state = self._state(entity_id)
            if mode == "off" or (state and state.state not in ("off", mode)):
                await self._ensure_off(entity_id)
        for entity_id, mode in desired.items():
            if mode == "off":
                continue
            state = self._state(entity_id)
            if state is None:
                self.errors[entity_id] = "unavailable"
                self.status = "device_unavailable"
                continue
            # Never reverse an AC without an observed off state.
            if state.state not in ("off", mode):
                self.status = "waiting_for_off"
                continue
            if entity_id in self.radiators and self.ac:
                ac_state = self._state(self.ac)
                safe = ac_state is not None and (
                    ac_state.state == "off" or (self.demand.ac_mode == "heat" and ac_state.state == "heat")
                )
                if not safe:
                    await self._ensure_off(entity_id)
                    self.status = "waiting_for_ac_off"
                    continue
            if entity_id == self.ac and mode == "cool" and not self._all_off(self.radiators):
                await self._ensure_off(entity_id)
                self.status = "waiting_for_radiators_off"
                continue
            if entity_id == self.ac and state.state == "off":
                if self.now() - self._ac_off_since < self.config["ac_cooldown_seconds"]:
                    self.status = "ac_cooldown"
                    continue
            if entity_id in self.radiators:
                if self._pid_active:
                    unit = state.attributes.get("temperature_unit", self.hass.config.units.temperature_unit)
                    local = state.attributes.get("current_temperature")
                    local = TemperatureConverter.convert(float(local), unit, UnitOfTemperature.CELSIUS) if isinstance(local, (float, int)) and isfinite(local) else self.temperature
                    minimum = TemperatureConverter.convert(float(state.attributes.get("min_temp", 5)), unit, UnitOfTemperature.CELSIUS)
                    maximum = TemperatureConverter.convert(float(state.attributes.get("max_temp", 35)), unit, UnitOfTemperature.CELSIUS)
                    native_step = float(state.attributes.get("target_temp_step", .5))
                    step_c = native_step / 1.8 if unit == UnitOfTemperature.FAHRENHEIT else native_step
                    value = TemperatureConverter.convert(trv_target(local, self.heat_output, minimum, maximum, step_c), UnitOfTemperature.CELSIUS, unit)
                    last = self._pid_last_sent.get(entity_id, float("-inf"))
                    if state.state == "heat" and self.now()-last < self.config["pid_update_seconds"]:
                        continue
                else:
                    value = float(state.attributes.get("max_temp", 30))
            else:
                # The external sensor owns the stop decision. Request full
                # heating/cooling demand rather than trusting the AC's sensor.
                unit = state.attributes.get("temperature_unit", self.hass.config.units.temperature_unit)
                fallback = TemperatureConverter.convert(30 if mode == "heat" else 16,
                                                        UnitOfTemperature.CELSIUS, unit)
                value = float(state.attributes.get("max_temp" if mode == "heat" else "min_temp", fallback))
            # Confirm the requested mode before setting a target: a target-only
            # command can implicitly resume the AC's previous (opposite) mode.
            if state.state != mode:
                await self._call(entity_id, "set_hvac_mode", {"hvac_mode": mode})
            state = self._state(entity_id)
            if state is None or state.state != mode:
                self.status = "waiting_for_device"
                continue
            if state.attributes.get("temperature") != value:
                if await self._call(entity_id, "set_temperature", {"temperature": value}):
                    if entity_id in self.radiators and self._pid_active:
                        self._pid_last_sent[entity_id] = self.now()
                else:
                    self.status = "waiting_for_device"
        if self.errors:
            self.status = "device_error"


"""Exercise the real command adapter against a small fake HA API.

These tests check command ordering and failure handling; they do not replace
loading the integration in a real Home Assistant instance.
"""

import importlib.util
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]


def stub(name, **attributes):
    module = ModuleType(name)
    module.__dict__.update(attributes)
    sys.modules[name] = module
    return module


class HomeAssistantError(Exception):
    pass


class FakeStore:
    def __init__(self, *args):
        self.saved = None

    async def async_load(self):
        return self.saved

    def async_delay_save(self, callback, delay):
        self.saved = callback()

    async def async_save(self, value):
        self.saved = value


class TemperatureConverter:
    @staticmethod
    def convert(value, source, target):
        if source == target:
            return value
        return (value - 32) * 5 / 9 if source == "°F" else value * 9 / 5 + 32


stub("homeassistant")
stub("homeassistant.const", STATE_UNAVAILABLE="unavailable", STATE_UNKNOWN="unknown",
     Platform=SimpleNamespace(CLIMATE="climate", BUTTON="button", SWITCH="switch", NUMBER="number", SELECT="select"),
     UnitOfTemperature=SimpleNamespace(CELSIUS="°C", FAHRENHEIT="°F"))
stub("homeassistant.core", callback=lambda f: f)
stub("homeassistant.exceptions", HomeAssistantError=HomeAssistantError)
stub("homeassistant.helpers")
stub("homeassistant.helpers.event", async_track_state_change_event=lambda *a: lambda: None,
     async_track_time_interval=lambda *a: lambda: None)
stub("homeassistant.helpers.storage", Store=FakeStore)
stub("homeassistant.util")
stub("homeassistant.util.unit_conversion", TemperatureConverter=TemperatureConverter)
package = stub("room_comfort_test")
package.__path__ = [str(ROOT / "custom_components/room_comfort")]
spec = importlib.util.spec_from_file_location("room_comfort_test.controller", Path(package.__path__[0]) / "controller.py")
controller_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = controller_module
spec.loader.exec_module(controller_module)
RoomController = controller_module.RoomController


def state(value, **attributes):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(state=value, attributes=attributes, last_updated=now, last_reported=now)


class FakeServices:
    def __init__(self, states):
        self.states = states
        self.calls = []
        self.fail = set()
        self.lag = set()

    async def async_call(self, domain, service, data, blocking):
        self.calls.append((service, data.copy()))
        eid = data["entity_id"]
        if eid in self.fail:
            raise HomeAssistantError("simulated device failure")
        if eid in self.lag:
            return
        if service == "set_hvac_mode":
            self.states[eid].state = data["hvac_mode"]
        if service == "set_temperature":
            self.states[eid].attributes["temperature"] = data["temperature"]


class ControllerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.states = {
            "sensor.room": state("19", unit_of_measurement="°C"),
            "climate.r1": state("off", min_temp=5, max_temp=35, temperature=21),
            "climate.r2": state("off", min_temp=5, max_temp=35, temperature=21),
            "climate.ac": state("off", min_temp=16, max_temp=30, temperature=21),
        }
        self.services = FakeServices(self.states)
        self.hass = SimpleNamespace(states=SimpleNamespace(get=self.states.get), services=self.services,
                                    config=SimpleNamespace(units=SimpleNamespace(temperature_unit="°C")))
        self.entry = SimpleNamespace(entry_id="room1", options={}, data={
            "control_method": "hysteresis",
            "name": "Salon", "temperature_sensor": "sensor.room",
            "radiators": ["climate.r1", "climate.r2"], "air_conditioner": "climate.ac",
        })
        self.room = RoomController(self.hass, self.entry)
        self.clock = self.room.now()
        self.room.now = lambda: self.clock
        self.room._ac_off_since = self.clock - 200

    async def heat(self):
        await self.room.async_change(enabled=True, mode="heat")

    async def test_observe_only_sends_no_commands(self):
        await self.room.async_change(mode="heat")
        self.assertEqual(self.services.calls, [])
        self.assertEqual(self.room.status, "observe_only")
        self.assertTrue(self.room.demand.radiator_heat)

    async def test_heat_opens_both_valves(self):
        await self.heat()
        for eid in self.room.radiators:
            self.assertEqual(self.states[eid].state, "heat")
            self.assertEqual(self.states[eid].attributes["temperature"], 35)
        self.assertEqual(self.states["climate.ac"].state, "off")

    async def test_sensor_failure_closes_all_devices(self):
        await self.heat()
        self.states["sensor.room"].state = "unavailable"
        await self.room.async_evaluate()
        self.assertTrue(all(self.states[e].state == "off" for e in self.room.devices))
        self.assertEqual(self.room.status, "sensor_unavailable")

    async def test_stale_sensor_stops_demand(self):
        self.states["sensor.room"].last_reported -= timedelta(hours=2)
        await self.heat()
        self.assertEqual(self.room.status, "sensor_unavailable")
        self.assertFalse(self.room.demand.radiator_heat)

    async def test_fahrenheit_sensor(self):
        self.states["sensor.room"] = state("68", unit_of_measurement="°F")
        self.assertAlmostEqual(self.room.temperature, 20)

    async def test_unknown_unit_is_not_assumed_celsius(self):
        self.states["sensor.room"].attributes["unit_of_measurement"] = "K"
        self.assertIsNone(self.room.temperature)

    async def test_cooling_waits_for_confirmed_radiators_off(self):
        self.states["sensor.room"].state = "25"
        self.states["climate.r1"].state = "heat"
        self.services.lag.add("climate.r1")
        await self.room.async_change(enabled=True, mode="cool")
        self.assertEqual(self.states["climate.ac"].state, "off")
        self.assertEqual(self.room.status, "waiting_for_radiators_off")

    async def test_cooling_waits_for_unavailable_radiator(self):
        self.states["sensor.room"].state = "25"
        self.states["climate.r2"].state = "unavailable"
        await self.room.async_change(enabled=True, mode="cool")
        self.assertEqual(self.states["climate.ac"].state, "off")

    async def test_heating_waits_for_cooling_ac_to_stop(self):
        self.states["climate.ac"].state = "cool"
        self.services.lag.add("climate.ac")
        await self.heat()
        self.assertEqual(self.states["climate.r1"].state, "off")
        self.assertEqual(self.states["climate.r2"].state, "off")

    async def test_existing_radiator_heat_stops_if_cooling_cannot_be_stopped(self):
        self.states["climate.r1"].state = "heat"
        self.states["climate.ac"].state = "cool"
        self.services.lag.add("climate.ac")
        await self.heat()
        self.assertEqual(self.states["climate.r1"].state, "off")

    async def test_existing_ac_cooling_stops_if_radiator_cannot_be_stopped(self):
        self.states["sensor.room"].state = "25"
        self.states["climate.ac"].state = "cool"
        self.states["climate.r1"].state = "heat"
        self.services.lag.add("climate.r1")
        await self.room.async_change(enabled=True, mode="cool")
        self.assertEqual(self.states["climate.ac"].state, "off")

    async def test_off_failure_prevents_opposite_start(self):
        self.states["climate.ac"].state = "cool"
        self.services.fail.add("climate.ac")
        await self.heat()
        self.assertEqual(self.states["climate.r1"].state, "off")
        self.assertIn("climate.ac", self.room.errors)

    async def test_ac_mode_confirmed_before_target(self):
        self.states["sensor.room"].state = "25"
        await self.room.async_change(enabled=True, mode="cool", target=22)
        calls = [(service, data) for service, data in self.services.calls if data["entity_id"] == "climate.ac"]
        self.assertEqual(calls[0][0], "set_hvac_mode")
        self.assertEqual(calls[0][1]["hvac_mode"], "cool")
        self.assertEqual(calls[1][0], "set_temperature")

    async def test_no_target_sent_until_mode_confirmed(self):
        self.states["sensor.room"].state = "25"
        self.services.lag.add("climate.ac")
        await self.room.async_change(enabled=True, mode="cool", target=22)
        self.assertFalse(any(s == "set_temperature" and d["entity_id"] == "climate.ac" for s, d in self.services.calls))

    async def test_ac_changeover_has_cooldown(self):
        self.states["climate.ac"].state = "heat"
        self.room._last_ac_mode = "heat"
        self.states["sensor.room"].state = "25"
        await self.room.async_change(enabled=True, mode="cool")
        self.assertEqual(self.states["climate.ac"].state, "off")
        self.assertEqual(self.room.status, "ac_cooldown")
        self.clock += 181
        await self.room.async_evaluate()
        self.assertEqual(self.states["climate.ac"].state, "cool")

    async def test_boost_times_out_and_returns_to_radiators(self):
        await self.heat()
        await self.room.async_boost()
        self.assertEqual(self.states["climate.ac"].state, "heat")
        self.clock += 1201
        await self.room.async_evaluate()
        self.assertIsNone(self.room.boost_until)
        self.assertEqual(self.states["climate.ac"].state, "off")
        self.assertEqual(self.states["climate.r1"].state, "heat")

    async def test_boost_finishes_at_target_and_does_not_restart(self):
        await self.heat()
        await self.room.async_boost()
        self.states["sensor.room"].state = "21"
        await self.room.async_evaluate()
        self.assertIsNone(self.room.boost_until)
        self.states["sensor.room"].state = "19"
        self.clock += 31
        await self.room.async_evaluate()
        self.assertEqual(self.states["climate.ac"].state, "off")
        self.assertEqual(self.states["climate.r1"].state, "heat")

    async def test_boost_unavailable_raises(self):
        self.states["climate.ac"].state = "unavailable"
        with self.assertRaises(HomeAssistantError):
            await self.room.async_boost()

    async def test_duplicate_commands_rate_limited(self):
        self.services.lag.add("climate.r1")
        await self.heat()
        count = len(self.services.calls)
        await self.room.async_evaluate()
        self.assertEqual(len(self.services.calls), count)

    async def test_one_failed_radiator_does_not_abort_other(self):
        self.services.fail.add("climate.r1")
        await self.heat()
        self.assertEqual(self.states["climate.r2"].state, "heat")

    async def test_disabling_stops_all_outputs(self):
        await self.heat()
        await self.room.async_change(enabled=False)
        self.assertTrue(all(self.states[e].state == "off" for e in self.room.devices))
        self.assertEqual(self.room.status, "observe_only")

    async def test_failed_disable_keeps_retrying_and_surfaces_error(self):
        await self.heat()
        self.services.fail.add("climate.r1")
        await self.room.async_change(enabled=False)
        self.assertEqual(self.room.status, "stopping_devices")
        self.assertIn("climate.r1", self.room.errors)
        self.services.fail.clear()
        self.clock += 31
        await self.room.async_evaluate()
        self.assertEqual(self.room.status, "observe_only")
        self.assertEqual(self.states["climate.r1"].state, "off")

    async def test_restart_restores_target_but_not_boost(self):
        self.room._store.saved = {"mode": "heat", "target": 22.5, "enabled": True}
        await self.room.async_load()
        self.assertEqual(self.room.target, 22.5)
        self.assertTrue(self.room.enabled)
        self.assertIsNone(self.room.boost_until)

    async def test_unknown_window_pauses_heat(self):
        self.room.config["windows"] = ["binary_sensor.missing"]
        await self.heat()
        self.assertEqual(self.room.status, "window_open")

    async def test_no_ac_room_heats_independently(self):
        self.entry.data["air_conditioner"] = ""
        self.room = RoomController(self.hass, self.entry)
        await self.heat()
        self.assertEqual(self.states["climate.r1"].state, "heat")

    async def test_invalid_target_is_rejected(self):
        with self.assertRaises(HomeAssistantError):
            await self.room.async_change(target=float("nan"))

    async def test_pid_keeps_native_heat_and_never_uses_maximum_targets(self):
        self.room.config["control_method"] = "pid"
        for eid in self.room.radiators:
            self.states[eid].attributes["current_temperature"] = 22
        await self.heat()
        for eid in self.room.radiators:
            self.assertEqual(self.states[eid].state, "heat")
            self.assertLessEqual(self.states[eid].attributes["temperature"], 25)
        self.states["sensor.room"].state = "21"
        self.clock += 130
        await self.room.async_evaluate()
        self.assertTrue(all(self.states[e].state == "heat" for e in self.room.radiators))
        self.assertFalse(any(service == "set_hvac_mode" and data.get("hvac_mode") == "off" and data["entity_id"] in self.room.radiators for service, data in self.services.calls))

    async def test_pid_sensor_failure_still_forces_outputs_off(self):
        self.room.config["control_method"] = "pid"
        await self.heat()
        self.states["sensor.room"].state = "unavailable"
        await self.room.async_evaluate()
        self.assertEqual(self.room.heat_output, 0)
        self.assertTrue(all(self.states[e].state == "off" for e in self.room.radiators))

    async def test_pid_limits_native_target_update_rate(self):
        self.room.config["control_method"] = "pid"
        await self.heat()
        count = sum(service == "set_temperature" for service, data in self.services.calls)
        self.clock += 60
        self.states["sensor.room"].state = "20.5"
        await self.room.async_evaluate()
        self.assertEqual(sum(service == "set_temperature" for service, data in self.services.calls), count)

    async def test_household_changes_target_without_destroying_other_profiles(self):
        home = SimpleNamespace(profile="away")
        self.room.household = home
        self.assertEqual(self.room.target, 19)
        await self.room.async_change(target=19.5)
        self.assertEqual(self.room.targets["away"], 19.5)
        self.assertEqual(self.room.targets["home"], 21)
        home.profile = "prewarming"
        self.assertEqual(self.room.target, 21)

    async def test_heat_and_cool_keep_separate_profile_targets(self):
        await self.room.async_change(mode="cool")
        self.assertEqual(self.room.target, 24)
        await self.room.async_change(target=23.5)
        await self.room.async_change(mode="heat")
        self.assertEqual(self.room.target, 21)
        self.assertEqual(self.room.cool_targets["home"], 23.5)

    async def test_combined_mode_and_target_updates_requested_mode_only(self):
        await self.room.async_change(mode="cool", target=25)
        self.assertEqual(self.room.target, 25)
        self.assertEqual(self.room.targets["home"], 21)
        await self.room.async_change(mode="heat", target=22)
        self.assertEqual(self.room.cool_targets["home"], 25)
        self.assertEqual(self.room.targets["home"], 22)

    async def test_away_cooling_uses_warmer_limit(self):
        self.room.household = SimpleNamespace(profile="away")
        await self.room.async_change(mode="cool")
        self.assertEqual(self.room.target, 27)
        self.assertEqual(self.room.demand.ac_mode, "off")
        await self.room.async_set_profile_temperature("away", 26, "cool")
        self.assertEqual(self.room.target, 26)
        self.assertEqual(self.room.targets["away"], 19)

    async def test_coming_home_can_cool_with_radiators_off(self):
        await self.room.async_set_coming_home_mode("cool")
        self.room.household = SimpleNamespace(profile="prewarming")
        self.states["sensor.room"].state = "28"
        self.clock += 200
        await self.room.async_change(enabled=True)
        self.assertEqual(self.room.mode, "cool")
        self.assertEqual(self.room.target, 24)
        self.assertFalse(self.room.coming_home_ready)
        self.assertTrue(all(self.states[e].state == "off" for e in self.room.radiators))
        self.assertEqual(self.states["climate.ac"].state, "cool")
        self.states["sensor.room"].state = "24.1"
        self.assertTrue(self.room.coming_home_ready)

    async def test_coming_home_observe_only_never_changes_mode_or_devices(self):
        await self.room.async_set_coming_home_mode("cool")
        self.room.household = SimpleNamespace(profile="prewarming")
        await self.room.async_evaluate()
        self.assertEqual(self.room.mode, "off")
        self.assertEqual(self.services.calls, [])

    async def test_cooling_profile_and_return_mode_restore(self):
        await self.room.async_set_profile_temperature("home", 25, "cool")
        await self.room.async_set_coming_home_mode("cool")
        saved = self.room._store.saved
        restored = RoomController(self.hass, self.entry)
        restored._store.saved = saved
        await restored.async_load()
        self.assertEqual(restored.cool_targets["home"], 25)
        self.assertEqual(restored.coming_home_mode, "cool")

    async def test_no_ac_rejects_cooling_return_and_profile(self):
        self.entry.data["air_conditioner"] = ""
        room = RoomController(self.hass, self.entry)
        with self.assertRaises(HomeAssistantError):
            await room.async_set_coming_home_mode("cool")
        with self.assertRaises(HomeAssistantError):
            await room.async_set_profile_temperature("home", 25, "cool")


if __name__ == "__main__":
    unittest.main()


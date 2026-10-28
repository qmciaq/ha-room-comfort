"""PID dynamics and conservative household presence boundaries."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/room_comfort"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


pid = module("pid")
presence = module("presence")


class PIDTests(unittest.TestCase):
    def test_near_target_requests_partial_heat_not_full(self):
        p = pid.RoomPID()
        value = p.update(20.7, 21, 0)
        self.assertGreater(value, 0)
        self.assertLess(value, 1)

    def test_deadband_holds_stable_demand_without_integral_windup(self):
        p = pid.RoomPID()
        value = p.update(21, 21, 0)
        for minute in range(2, 90):
            self.assertEqual(p.update(21 + .05 * (-1)**minute, 21, minute*60), value)
        self.assertEqual(p.integral, 0)

    def test_heating_near_target_slews_down_gradually(self):
        p = pid.RoomPID()
        initial = p.update(18, 21, 0)
        result = p.update(20.8, 21, 60)
        self.assertGreater(result, 0)
        self.assertLess(result, initial)
        self.assertGreaterEqual(result, initial-.35)

    def test_warmup_output_is_not_latched_by_deadband(self):
        p = pid.RoomPID()
        self.assertEqual(p.update(17, 21, 0), 1)
        value = p.update(21, 21, 60)
        self.assertLess(value, 1)
        for minute in range(2, 12):
            value = p.update(21, 21, minute*60)
        self.assertLess(value, .5)

    def test_saturation_does_not_wind_up(self):
        p = pid.RoomPID()
        for minute in range(120):
            p.update(10, 25, minute*60)
        self.assertEqual(p.integral, 0)
        self.assertEqual(p.output, 1)

    def test_invalid_measurement_resets(self):
        p = pid.RoomPID()
        p.update(18, 21, 0)
        self.assertEqual(p.update(float("nan"), 21, 60), 0)

    def test_long_gap_does_not_integrate_downtime(self):
        p = pid.RoomPID(kp=0, ki=.01, kd=0)
        p.update(20, 21, 0)
        p.update(20, 21, 36000)
        self.assertLessEqual(p.integral, .02)

    def test_trv_target_uses_small_local_offset(self):
        self.assertEqual(pid.trv_target(24, .5, 5, 35), 24.5)
        self.assertEqual(pid.trv_target(24, 1, 5, 35), 27)
        self.assertEqual(pid.trv_target(24, 0, 5, 35), 22)

    def test_trv_target_clamps_and_rounds(self):
        self.assertEqual(pid.trv_target(33, 1, 5, 35), 35)
        self.assertEqual(pid.trv_target(5, 0, 5, 35), 5)

    def test_simple_thermal_model_settles_without_binary_power_cycles(self):
        p = pid.RoomPID()
        temperature, tail = 18.0, []
        for minute in range(240):
            power = p.update(temperature, 21, minute*60)
            temperature += .5*power-.015*(temperature-5)
            if minute >= 120:
                tail.append((temperature, power))
        self.assertLess(max(abs(t-21) for t, u in tail), .2)
        self.assertTrue(all(.1 < u < .9 for t, u in tail))


class PresenceTests(unittest.TestCase):
    zone = SimpleNamespace(state="0", attributes={"friendly_name": "Home", "latitude": 51, "longitude": 19, "radius": 100})

    def state(self, value, **attrs):
        return SimpleNamespace(state=value, attributes=attrs)

    def test_every_selected_tracker_must_be_known_outside(self):
        for values in ([], [None], [False, None], [False, True]):
            self.assertFalse(presence.all_outside(values))
        self.assertTrue(presence.all_outside([False, False]))

    def test_home_and_not_home(self):
        self.assertTrue(presence.zone_membership(self.state("home"), "zone.home", self.zone))
        self.assertFalse(presence.zone_membership(self.state("not_home"), "zone.home", self.zone))

    def test_unavailable_tracker_is_unknown(self):
        for value in (None, self.state("unknown"), self.state("unavailable")):
            self.assertIsNone(presence.zone_membership(value, "zone.home", self.zone))

    def test_in_zones_handles_overlapping_zones(self):
        self.assertTrue(presence.zone_membership(self.state("small", in_zones=["zone.small", "zone.home"]), "zone.home", self.zone))

    def test_custom_zone_without_position_is_not_assumed_away(self):
        self.assertIsNone(presence.zone_membership(self.state("not_home"), "zone.custom", self.zone))

    def test_gps_uncertainty_at_boundary_is_unknown(self):
        state = self.state("not_home", latitude=51.0009, longitude=19, gps_accuracy=30)
        self.assertIsNone(presence.zone_membership(state, "zone.custom", self.zone))

    def test_gps_inside_and_outside(self):
        self.assertTrue(presence.zone_membership(self.state("x", latitude=51, longitude=19), "zone.custom", self.zone))
        self.assertFalse(presence.zone_membership(self.state("x", latitude=52, longitude=19), "zone.custom", self.zone))

    def test_invalid_coordinates_are_unknown(self):
        self.assertIsNone(presence.zone_membership(self.state("x", latitude=float("nan"), longitude=19), "zone.custom", self.zone))

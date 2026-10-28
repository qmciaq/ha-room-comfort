"""Outdoor latches, window debounce and independent room absence timers."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components/room_comfort"


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


outdoor = module("outdoor")
conditions = module("room_conditions")


class OutdoorTests(unittest.TestCase):
    def setUp(self):
        self.gate = outdoor.OutdoorGate()
        self.settings = {**outdoor.OUTDOOR_DEFAULTS, "outdoor_enabled": True}

    def check(self, temperature, mode="heat"):
        return self.gate.evaluate(mode, temperature, self.settings)

    def test_heat_starts_strictly_below_16(self):
        self.assertEqual(self.check(18), "outdoor_heat_blocked")
        self.assertEqual(self.check(16), "outdoor_heat_blocked")
        self.assertIsNone(self.check(15.9))

    def test_heat_latch_prevents_chatter_and_stops_at_16_5(self):
        self.check(15)
        self.assertIsNone(self.check(16.4))
        self.assertEqual(self.check(16.5), "outdoor_heat_blocked")
        self.assertEqual(self.check(16.1), "outdoor_heat_blocked")

    def test_cool_starts_above_24_stops_at_23_5(self):
        self.assertEqual(self.check(24, "cool"), "outdoor_cool_blocked")
        self.assertIsNone(self.check(24.1, "cool"))
        self.assertIsNone(self.check(23.6, "cool"))
        self.assertEqual(self.check(23.5, "cool"), "outdoor_cool_blocked")

    def test_missing_nan_and_infinite_readings_block(self):
        for value in (None, float("nan"), float("inf")):
            self.assertEqual(self.check(value), "outdoor_unavailable")

    def test_disabled_and_off_do_not_need_a_sensor(self):
        self.settings["outdoor_enabled"] = False
        self.assertIsNone(self.check(None))
        self.settings["outdoor_enabled"] = True
        self.assertIsNone(self.check(None, "off"))

    def test_setting_change_resets_latches(self):
        self.check(15)
        self.settings["outdoor_heat_below"] = 14
        self.assertEqual(self.check(14.2), "outdoor_heat_blocked")


class RoomConditionTests(unittest.TestCase):
    def setUp(self):
        self.room = conditions.RoomConditions()
        self.args = dict(windows={}, presence={}, now=100, mode="heat", window_delay=10,
                         pause_heat=True, pause_cool=True, heat_minutes=30, cool_minutes=10)

    def evaluate(self, **values):
        return self.room.evaluate(**(self.args | values))

    def test_window_waits_ten_seconds_then_pauses(self):
        self.assertIsNone(self.evaluate(windows={"w": "on"}))
        self.assertEqual(self.room.next_check, 110)
        self.assertIsNone(self.evaluate(windows={"w": "on"}, now=109.9))
        self.assertEqual(self.evaluate(windows={"w": "on"}, now=110), "window_open")
        self.assertIsNone(self.evaluate(windows={"w": "off"}, now=111))

    def test_brief_opening_does_not_accumulate(self):
        self.evaluate(windows={"w": "on"})
        self.evaluate(windows={"w": "off"}, now=109)
        self.assertIsNone(self.evaluate(windows={"w": "on"}, now=115))
        self.assertEqual(self.room.next_check, 125)

    def test_each_contact_has_its_own_timer(self):
        self.evaluate(windows={"a": "on", "b": "off"})
        self.assertIsNone(self.evaluate(windows={"a": "off", "b": "on"}, now=109))
        self.assertEqual(self.room.next_check, 119)

    def test_unknown_window_blocks_immediately(self):
        self.assertEqual(self.evaluate(windows={"w": None}), "window_open")

    def test_room_heat_and_cool_have_independent_absence_delays(self):
        self.evaluate(presence={"p": "off"})
        self.assertIsNone(self.evaluate(presence={"p": "off"}, now=700))
        self.assertEqual(self.evaluate(presence={"p": "off"}, now=700, mode="cool"), "room_unoccupied")
        self.assertEqual(self.evaluate(presence={"p": "off"}, now=1900), "room_unoccupied")

    def test_all_sensors_must_be_clear(self):
        self.evaluate(presence={"a": "off", "b": "on"})
        self.assertTrue(self.room.occupied)
        self.assertIsNone(self.room.absent_since)

    def test_unknown_presence_preserves_comfort_resets_timer(self):
        self.evaluate(presence={"a": "off"})
        self.assertIsNone(self.evaluate(presence={"a": "off", "b": None}, now=9999))
        self.assertIsNone(self.room.occupied)
        self.assertIsNone(self.room.absent_since)

    def test_presence_return_resumes_immediately(self):
        self.evaluate(presence={"a": "off"})
        self.evaluate(presence={"a": "off"}, now=2000)
        self.assertIsNone(self.evaluate(presence={"a": "on"}, now=2001))

    def test_absence_pausing_can_be_disabled_per_mode(self):
        self.assertIsNone(self.evaluate(presence={"p": "off"}, pause_heat=False, heat_minutes=0))
        self.assertEqual(self.evaluate(presence={"p": "off"}, mode="cool", cool_minutes=0), "room_unoccupied")

    def test_no_presence_selection_never_means_empty(self):
        self.assertIsNone(self.evaluate(now=999999))
        self.assertIsNone(self.room.absent_since)

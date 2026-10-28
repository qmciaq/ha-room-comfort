"""Control decisions, boundaries, and one-shot boost semantics."""

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("comfort_engine", ROOT / "custom_components/room_comfort/engine.py")
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)
Demand = engine.Demand


class EngineTests(unittest.TestCase):
    def demand(self, **overrides):
        args = dict(mode="heat", temperature=19.0, target=21.0, tolerance=0.3,
                    previous=Demand(), boost_until=None, now=1000)
        return engine.calculate_demand(**(args | overrides))

    def test_heat_starts_below_band(self):
        self.assertTrue(self.demand().radiator_heat)

    def test_heat_does_not_start_inside_band(self):
        self.assertFalse(self.demand(temperature=20.8).radiator_heat)

    def test_heat_keeps_running_inside_band(self):
        self.assertTrue(self.demand(temperature=20.8, previous=Demand(radiator_heat=True)).radiator_heat)

    def test_heat_stops_at_target(self):
        self.assertFalse(self.demand(temperature=21, previous=Demand(radiator_heat=True)).radiator_heat)

    def test_cooling_starts(self):
        result = self.demand(mode="cool", temperature=23)
        self.assertEqual(result.ac_mode, "cool")
        self.assertFalse(result.radiator_heat)

    def test_cooling_does_not_start_inside_band(self):
        self.assertEqual(self.demand(mode="cool", temperature=21.2).ac_mode, "off")

    def test_cooling_keeps_running_inside_band(self):
        self.assertEqual(self.demand(mode="cool", temperature=21.2, previous=Demand(ac_mode="cool")).ac_mode, "cool")

    def test_cooling_stops_at_target(self):
        self.assertEqual(self.demand(mode="cool", temperature=21, previous=Demand(ac_mode="cool")).ac_mode, "off")

    def test_radiators_only_never_starts_ac(self):
        self.assertEqual(self.demand().ac_mode, "off")

    def test_boost_heats_with_both_sources(self):
        result = self.demand(boost_until=1500)
        self.assertEqual(result.ac_mode, "heat")
        self.assertTrue(result.radiator_heat)

    def test_boost_stops_at_target(self):
        result = self.demand(temperature=21, boost_until=1500)
        self.assertTrue(result.boost_finished)
        self.assertEqual(result.ac_mode, "off")

    def test_boost_times_out_but_radiators_continue(self):
        result = self.demand(boost_until=1000)
        self.assertTrue(result.boost_finished)
        self.assertTrue(result.radiator_heat)
        self.assertEqual(result.ac_mode, "off")

    def test_off_cancels_boost(self):
        self.assertEqual(self.demand(mode="off", boost_until=1500), Demand(boost_finished=True))

    def test_invalid_sensor_fails_closed(self):
        for value in (None, float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                result = self.demand(temperature=value, boost_until=1500)
                self.assertEqual(result.status, "sensor_unavailable")
                self.assertFalse(result.radiator_heat)
                self.assertEqual(result.ac_mode, "off")
                self.assertTrue(result.boost_finished)

    def test_window_cancels_boost_and_heating(self):
        result = self.demand(window_open=True, boost_until=1500)
        self.assertEqual(result.status, "window_open")
        self.assertFalse(result.radiator_heat)
        self.assertTrue(result.boost_finished)

    def test_cooling_cancels_heat_boost(self):
        self.assertTrue(self.demand(mode="cool", temperature=24, boost_until=1500).boost_finished)

    def test_invalid_mode_is_off(self):
        self.assertEqual(self.demand(mode="bogus").status, "invalid_mode")

    def test_heat_never_outputs_cooling_across_temperatures(self):
        for temp in range(-10, 61):
            self.assertNotEqual(self.demand(temperature=temp, boost_until=1500).ac_mode, "cool")


if __name__ == "__main__":
    unittest.main()

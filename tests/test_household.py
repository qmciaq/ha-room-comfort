"""Manual vacation, all-outside detection, return and prewarm expiry."""

import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

# Reuse the fake API scaffolding while importing the real new controller.
from test_controller import RoomController, FakeStore, stub

stub("homeassistant.core", callback=lambda f: f)
ROOT = Path(__file__).resolve().parents[1] / "custom_components/room_comfort"
spec = importlib.util.spec_from_file_location("room_comfort_test.household", ROOT / "household.py")
household = importlib.util.module_from_spec(spec)
spec.loader.exec_module(household)


class HouseholdTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.states = {"zone.home": SimpleNamespace(state="0", attributes={"friendly_name": "Home"}),
                       "person.a": SimpleNamespace(state="not_home", attributes={}),
                       "device_tracker.b": SimpleNamespace(state="not_home", attributes={})}
        self.hass = SimpleNamespace(states=SimpleNamespace(get=self.states.get))
        self.home = household.Household(self.hass)
        self.home.config.update(presence_entities=["person.a", "device_tracker.b"], away_delay_minutes=5)
        self.clock = 1000
        self.home.now = lambda: self.clock

    async def test_away_requires_every_tracker_and_confirmation_delay(self):
        await self.home.async_evaluate()
        self.assertEqual(self.home.profile, "home")
        self.clock += 301
        await self.home.async_evaluate()
        self.assertEqual(self.home.profile, "away")
        self.states["person.a"].state = "home"
        await self.home.async_evaluate()
        self.assertEqual(self.home.profile, "home")

    async def test_unknown_tracker_protects_comfort_and_resets_delay(self):
        await self.home.async_evaluate()
        self.clock += 301
        self.states["person.a"].state = "unknown"
        await self.home.async_evaluate()
        self.assertEqual(self.home.profile, "home")
        self.assertIsNone(self.home.away_since)

    async def test_vacation_requires_manual_action_and_does_not_auto_clear(self):
        await self.home.async_change("vacation", True)
        self.states["person.a"].state = "home"
        await self.home.async_evaluate()
        self.assertEqual(self.home.profile, "vacation")
        await self.home.async_change("vacation", False)
        self.assertEqual(self.home.profile, "home")

    async def test_coming_home_clears_vacation_and_uses_home_targets(self):
        await self.home.async_change("vacation", True)
        await self.home.async_change("coming_home", True)
        self.assertFalse(self.home.vacation)
        self.assertEqual(self.home.profile, "prewarming")

    async def test_prewarm_remains_on_when_ready_until_arrival(self):
        room = SimpleNamespace(enabled=True, temperature=21, targets={"home": 21}, coming_home_ready=True)
        self.home.rooms = [room]
        await self.home.async_change("coming_home", True)
        self.assertTrue(self.home.prewarm_ready)
        self.assertTrue(self.home.prewarming)
        self.states["person.a"].state = "home"
        await self.home.async_evaluate()
        self.assertFalse(self.home.prewarming)
        self.assertEqual(self.home.profile, "home")

    async def test_prewarm_timeout_returns_to_away(self):
        self.home.config["away_delay_minutes"] = 0
        await self.home.async_change("coming_home", True)
        self.clock += 4*3600+1
        await self.home.async_evaluate()
        self.assertFalse(self.home.prewarming)
        self.assertEqual(self.home.profile, "away")

    async def test_empty_tracker_selection_never_means_away(self):
        self.home.config["presence_entities"] = []
        self.clock += 9999
        await self.home.async_evaluate()
        self.assertEqual(self.home.profile, "home")

    async def test_disabling_auto_away_keeps_home(self):
        self.home.config["away_delay_minutes"] = 0
        await self.home.async_evaluate()
        self.assertEqual(self.home.profile, "away")
        await self.home.async_change("automatic_away", False)
        self.assertEqual(self.home.profile, "home")

    async def test_manual_state_restores_across_restart(self):
        await self.home.async_change("vacation", True)
        saved = self.home._store.saved
        other = household.Household(self.hass)
        other._store.saved = saved
        await other.async_load()
        self.assertTrue(other.vacation)


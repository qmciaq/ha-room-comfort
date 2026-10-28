"""Shared home/away/vacation/prewarm modes for all room controllers."""

import asyncio
from datetime import timedelta
import time

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .presence import all_outside, zone_membership
from .outdoor import OUTDOOR_DEFAULTS

HOUSE_DEFAULTS = {**OUTDOOR_DEFAULTS, "presence_entities": [], "home_zone": "zone.home",
                  "away_delay_minutes": 5, "prewarm_hours": 4}


async def async_get_household(hass):
    data = hass.data.setdefault(DOMAIN, {})
    async with data.setdefault("household_lock", asyncio.Lock()):
        if "household" not in data:
            controller = Household(hass)
            await controller.async_load()
            data["household"] = controller
        return data["household"]


class Household:
    def __init__(self, hass):
        self.hass = hass
        self.config = dict(HOUSE_DEFAULTS)
        self.entity_ids = {}
        self.rooms = set()
        self._listeners = set()
        self._unsubscribers = []
        self._store = Store(hass, 1, f"{DOMAIN}.household")
        self.vacation = False
        self.automatic_away = True
        self.prewarm_until = None
        self.away_since = None
        self.profile = "home"
        self.memberships = {}
        self._was_inside = False
        self._lock = asyncio.Lock()
        self.now = time.time

    async def async_load(self):
        saved = await self._store.async_load() or {}
        self.vacation = bool(saved.get("vacation", False))
        self.automatic_away = bool(saved.get("automatic_away", True))
        self.prewarm_until = saved.get("prewarm_until")
        if not isinstance(self.prewarm_until, (int, float)) or self.prewarm_until <= self.now():
            self.prewarm_until = None

    def _settings(self):
        return {"vacation": self.vacation, "automatic_away": self.automatic_away,
                "prewarm_until": self.prewarm_until}

    @callback
    def async_subscribe(self, listener):
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    @callback
    def _publish(self):
        for listener in tuple(self._listeners):
            listener()

    async def async_configure(self, config):
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        self.config = {**HOUSE_DEFAULTS, **config}
        self.away_since = None
        watched = [self.config["home_zone"], *self.config["presence_entities"], self.config["outdoor_sensor"]]
        watched = [entity_id for entity_id in watched if entity_id]
        self._unsubscribers = [
            async_track_state_change_event(self.hass, watched, self._schedule),
            async_track_time_interval(self.hass, self._schedule, timedelta(seconds=30)),
        ]
        await self.async_evaluate()

    @callback
    def _schedule(self, event=None):
        self.hass.async_create_task(self.async_evaluate())

    @property
    def prewarming(self):
        return self.prewarm_until is not None and self.prewarm_until > self.now()

    @property
    def prewarm_ready(self):
        controlled = [r for r in self.rooms if r.enabled]
        return bool(controlled) and all(r.coming_home_ready and not getattr(r, "errors", {})
            and getattr(getattr(r, "demand", None), "status", None) not in ("sensor_unavailable", "window_open", "outdoor_unavailable")
            for r in controlled)

    async def async_change(self, key, enabled):
        async with self._lock:
            if key == "vacation":
                self.vacation = bool(enabled)
                if enabled:
                    self.prewarm_until = None
            elif key == "coming_home":
                self.prewarm_until = self.now() + self.config["prewarm_hours"] * 3600 if enabled else None
                if enabled:
                    self.vacation = False
            elif key == "automatic_away":
                self.automatic_away = bool(enabled)
                self.away_since = None
            else:
                raise ValueError(key)
            await self._store.async_save(self._settings())
        await self.async_evaluate()

    async def async_evaluate(self):
        async with self._lock:
            zone = self.hass.states.get(self.config["home_zone"])
            self.memberships = {entity_id: zone_membership(self.hass.states.get(entity_id),
                self.config["home_zone"], zone) for entity_id in self.config["presence_entities"]}
            inside = any(value is True for value in self.memberships.values())
            outside = self.automatic_away and all_outside(list(self.memberships.values()))
            if outside:
                if self.away_since is None:
                    self.away_since = self.now()
            else:
                self.away_since = None
            away = self.away_since is not None and self.now()-self.away_since >= self.config["away_delay_minutes"]*60
            if self.prewarm_until is not None and (self.prewarm_until <= self.now() or inside and not self._was_inside):
                self.prewarm_until = None
                await self._store.async_save(self._settings())
            self._was_inside = inside
            self.profile = "prewarming" if self.prewarming else "vacation" if self.vacation else "away" if away else "home"
            self._publish()

    async def async_stop(self):
        for unsubscribe in self._unsubscribers:
            unsubscribe()
        self._unsubscribers.clear()
        await self._store.async_save(self._settings())


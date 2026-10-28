"""Outdoor heating/cooling eligibility with separate hysteresis latches."""

from math import isfinite

OUTDOOR_DEFAULTS = {
    "outdoor_enabled": False,
    "outdoor_sensor": "",
    "outdoor_heat_below": 16.0,
    "outdoor_cool_above": 24.0,
    "outdoor_hysteresis": .5,
    "outdoor_timeout_minutes": 120,
}


class OutdoorGate:
    def __init__(self):
        self._settings = None
        self._heat = False
        self._cool = False

    def evaluate(self, mode, temperature, settings):
        """Return None when eligible; otherwise a readable blocking status.

        Heat starts strictly below its limit, stops at limit + hysteresis.
        Cool starts strictly above its limit, stops at limit - hysteresis.
        Invalid readings close both gates. No latch is restored across restart.
        """
        identity = tuple(sorted(settings.items()))
        if identity != self._settings:
            self._settings = identity
            self._heat = self._cool = False
        if not settings.get("outdoor_enabled") or mode == "off":
            return None
        if temperature is None or not isfinite(temperature):
            self._heat = self._cool = False
            return "outdoor_unavailable"
        heat, cool, band = (settings[k] for k in
                            ("outdoor_heat_below", "outdoor_cool_above", "outdoor_hysteresis"))
        self._heat = temperature < heat + (band if self._heat else 0)
        self._cool = temperature > cool - (band if self._cool else 0)
        if mode == "heat" and not self._heat:
            return "outdoor_heat_blocked"
        if mode == "cool" and not self._cool:
            return "outdoor_cool_blocked"
        return None

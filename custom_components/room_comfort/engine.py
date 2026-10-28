"""Deterministic room demand logic. No Home Assistant dependencies."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Demand:
    radiator_heat: bool = False
    ac_mode: str = "off"
    status: str = "off"
    boost_finished: bool = False


def calculate_demand(
    *, mode: str, temperature: float | None, target: float,
    tolerance: float, previous: Demand, boost_until: float | None,
    now: float, window_open: bool = False,
) -> Demand:
    """Use an external sensor, hysteresis, and a bounded one-shot boost.

    Heat starts below target minus tolerance, stops at target. Cooling
    starts above target plus tolerance, stops at target. A finished boost
    cannot restart without an explicit user action.
    """
    if mode == "off":
        return Demand(boost_finished=boost_until is not None)
    if temperature is None or not isfinite(temperature):
        return Demand(status="sensor_unavailable", boost_finished=boost_until is not None)
    if window_open:
        return Demand(status="window_open", boost_finished=boost_until is not None)
    if mode == "cool":
        cooling = temperature > target + tolerance or (
            previous.ac_mode == "cool" and temperature > target
        )
        return Demand(ac_mode="cool" if cooling else "off",
                      status="cooling" if cooling else "idle",
                      boost_finished=boost_until is not None)
    if mode != "heat":
        return Demand(status="invalid_mode", boost_finished=boost_until is not None)
    heating = temperature < target - tolerance or (
        (previous.radiator_heat or previous.ac_mode == "heat") and temperature < target
    )
    finished = boost_until is not None and (now >= boost_until or temperature >= target)
    boost = boost_until is not None and not finished
    return Demand(
        radiator_heat=heating,
        ac_mode="heat" if boost and heating else "off",
        status="boosting" if boost and heating else "heating" if heating else "idle",
        boost_finished=finished,
    )

"""Conservative zone membership; unknown is never proof of absence."""

from math import asin, cos, isfinite, radians, sin, sqrt


def zone_membership(state, zone_id, zone):
    """Return True/False/None for inside/outside/unknown."""
    if state is None or state.state in ("unknown", "unavailable") or zone is None:
        return None
    if zone_id == "zone.home" and state.state == "home":
        return True
    zones = state.attributes.get("in_zones")
    if isinstance(zones, (list, tuple)):
        return zone_id in zones
    if zone_id == "zone.home":
        if state.state == "not_home":
            return False
    name = zone.attributes.get("friendly_name")
    if name and state.state.casefold() == name.casefold():
        return True
    try:
        lat, lon = float(state.attributes["latitude"]), float(state.attributes["longitude"])
        zlat, zlon = float(zone.attributes["latitude"]), float(zone.attributes["longitude"])
        radius = float(zone.attributes.get("radius", 100))
        accuracy = max(0.0, float(state.attributes.get("gps_accuracy", 0)))
        if not all(isfinite(v) for v in (lat, lon, zlat, zlon, radius, accuracy)) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        dlat, dlon = radians(lat-zlat), radians(lon-zlon)
        a = sin(dlat/2)**2 + cos(radians(lat))*cos(radians(zlat))*sin(dlon/2)**2
        distance = 6371000 * 2 * asin(min(1.0, sqrt(max(0.0, a))))
        if distance + accuracy <= radius:
            return True
        if distance - accuracy > radius:
            return False
        return None
    except (TypeError, ValueError, KeyError):
        # A named different zone is useful for Home, but arbitrary connection
        # trackers cannot prove absence from an unrelated custom zone.
        if zone_id == "zone.home" and state.state not in ("", "unknown", "unavailable"):
            return False
        return None


def all_outside(memberships):
    return bool(memberships) and all(value is False for value in memberships)

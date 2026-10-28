"""Serve the bundled room cards and register the Room Comfort sidebar page."""

import asyncio
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url, async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.panel_custom import async_register_panel

from .const import DOMAIN, VERSION

URL = f"/room_comfort_frontend/room-comfort.js?v={VERSION}"


async def async_register_frontend(hass):
    """Keep all frontend files within the HACS-managed integration folder."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    lock = domain_data.setdefault("frontend_lock", asyncio.Lock())
    async with lock:
        await _async_register_frontend_locked(hass, domain_data)


async def _async_register_frontend_locked(hass, domain_data):
    """Avoid duplicate HTTP routes when several rooms start concurrently."""
    if not domain_data.get("static_registered"):
        await hass.http.async_register_static_paths([
            StaticPathConfig(
                "/room_comfort_frontend",
                str(Path(__file__).parent / "frontend"),
                cache_headers=False,
            )
        ])
        add_extra_js_url(hass, URL)
        domain_data["static_registered"] = True
    if not domain_data.get("panel_registered"):
        await async_register_panel(
            hass,
            webcomponent_name="room-comfort-panel",
            frontend_url_path="room-comfort",
            sidebar_title="Room Comfort",
            sidebar_icon="mdi:home-thermometer-outline",
            module_url=URL,
            embed_iframe=False,
            require_admin=False,
        )
        domain_data["panel_registered"] = True


def async_unregister_panel(hass):
    """Remove the sidebar when the last room is unloaded."""
    data = hass.data.get(DOMAIN, {})
    if data.get("panel_registered"):
        async_remove_panel(hass, "room-comfort")
        data["panel_registered"] = False

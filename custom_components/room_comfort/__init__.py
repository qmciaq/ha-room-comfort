"""One room thermostat coordinating radiators and an air conditioner."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN, PLATFORMS
from .controller import RoomController
from .frontend import async_register_frontend, async_unregister_panel
from .household import async_get_household


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one independent room."""
    household = await async_get_household(hass)
    if entry.data.get("kind") == "household":
        entry.runtime_data = household
        await household.async_configure({**entry.data, **entry.options})
        await hass.config_entries.async_forward_entry_setups(entry, [Platform.SWITCH, Platform.SENSOR])
        household._publish()
        return True
    if not any(e.data.get("kind") == "household" for e in hass.config_entries.async_entries(DOMAIN)):
        await hass.config_entries.flow.async_init(DOMAIN, context={"source": "import"}, data={"kind": "household"})
    controller = RoomController(hass, entry, household)
    entry.runtime_data = controller
    await controller.async_load()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # All entity IDs are now known. Publish the complete frontend links before
    # room setup finishes rather than waiting for the first background tick.
    await controller.async_evaluate()
    await async_register_frontend(hass)
    hass.data.setdefault(DOMAIN, {}).setdefault("rooms", set()).add(entry.entry_id)
    controller.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop our outputs before unloading a room."""
    controller = entry.runtime_data
    if entry.data.get("kind") == "household":
        await controller.async_stop()
        return await hass.config_entries.async_unload_platforms(entry, [Platform.SWITCH, Platform.SENSOR])
    await controller.async_stop()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        rooms = hass.data.get(DOMAIN, {}).get("rooms", set())
        rooms.discard(entry.entry_id)
        if not rooms:
            async_unregister_panel(hass)
    return unloaded

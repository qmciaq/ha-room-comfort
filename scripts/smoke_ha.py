"""Load a room in an isolated real HA Core runtime, with simulated devices.

Optional development check: run with the intended HA version installed.
It never uses the live Home Assistant instance or credentials.
"""

import asyncio
import importlib.metadata
import logging
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch


async def main():
    from homeassistant.core import HomeAssistant
    from homeassistant.auth import auth_manager_from_config
    from homeassistant.bootstrap import async_load_base_functionality
    from homeassistant.config_entries import ConfigEntries
    from homeassistant.setup import async_setup_component
    from aiohttp import ClientSession

    with tempfile.TemporaryDirectory(prefix="room-comfort-core-") as directory:
        target = Path(directory) / "custom_components/room_comfort"
        target.parent.mkdir()
        shutil.copytree(Path(__file__).resolve().parents[1] / "custom_components/room_comfort", target)
        hass = HomeAssistant(directory)
        try:
            from homeassistant import loader
            loader.async_setup(hass)
            hass.config_entries = ConfigEntries(hass, {})
            assert await async_load_base_functionality(hass)
            hass.auth = await auth_manager_from_config(hass, [], [])
            assert await async_setup_component(hass, "homeassistant", {})
            assert await async_setup_component(hass, "http", {"http": {"server_port": 8899}})
            hass.states.async_set("sensor.test_room", "19.8", {
                "device_class": "temperature", "unit_of_measurement": "°C",
            })
            for entity_id in ("climate.test_radiator_1", "climate.test_radiator_2"):
                hass.states.async_set(entity_id, "off", {
                    "hvac_modes": ["off", "heat"], "min_temp": 5,
                    "max_temp": 35, "temperature": 21, "supported_features": 1,
                })
            hass.states.async_set("climate.test_ac", "off", {
                "hvac_modes": ["off", "heat", "cool"], "min_temp": 16,
                "max_temp": 30, "temperature": 21, "supported_features": 1,
            })
            flow = await hass.config_entries.flow.async_init("room_comfort", context={"source": "user"})
            assert flow["type"] == "form", flow
            result = await hass.config_entries.flow.async_configure(flow["flow_id"], {
                "name": "Test room", "temperature_sensor": "sensor.test_room",
                "radiators": ["climate.test_radiator_1", "climate.test_radiator_2"],
                "air_conditioner": "climate.test_ac", "windows": [],
                "tolerance": 0.3, "boost_minutes": 20,
                "ac_cooldown_seconds": 180, "sensor_timeout_minutes": 60,
            })
            assert result["type"] == "create_entry", result
            await hass.async_block_till_done()
            rooms = [state for state in hass.states.async_all("climate") if state.attributes.get("room_comfort")]
            assert len(rooms) == 1, [(s.entity_id, s.state, s.attributes) for s in hass.states.async_all("climate")]
            room = rooms[0]
            assert room.attributes["control_switch"]
            assert room.attributes["cancel_boost_button"]
            assert room.attributes["current_temperature"] == 19.8
            assert room.attributes["control_devices"] is False
            assert "room-comfort" in hass.data["frontend_panels"]
            await hass.services.async_call("climate", "set_temperature", {
                "entity_id": room.entity_id, "temperature": 22,
            }, blocking=True)
            await hass.services.async_call("climate", "set_hvac_mode", {
                "entity_id": room.entity_id, "hvac_mode": "heat",
            }, blocking=True)
            await hass.async_block_till_done()
            updated = hass.states.get(room.entity_id)
            assert updated.attributes["temperature"] == 22
            assert updated.attributes["desired_radiator_heat"] is True
            assert hass.states.get("climate.test_radiator_1").state == "off"
            # The card's public JavaScript must actually be served, not just registered.
            async with ClientSession() as session:
                async with session.get("http://127.0.0.1:8899/room_comfort_frontend/room-comfort.js?v=0.3.0") as response:
                    assert response.status == 200, response.status
                    assert "room-comfort-card" in await response.text()
            # Exercise the real options form and room reload with settings intact.
            entry = result["result"]
            options = await hass.config_entries.options.async_init(entry.entry_id)
            assert options["type"] == "form", options
            updated_options = {**entry.data, "boost_minutes": 25, "home_temperature": 22}
            changed = await hass.config_entries.options.async_configure(options["flow_id"], updated_options)
            assert changed["type"] == "create_entry", changed
            await hass.async_block_till_done()
            assert entry.runtime_data.config["boost_minutes"] == 25
            assert entry.runtime_data.target == 22
            assert entry.runtime_data.mode == "heat"
            household = next(e for e in hass.config_entries.async_entries("room_comfort") if e.data.get("kind") == "household")
            home = household.runtime_data
            assert home.entity_ids["vacation"]
            await hass.services.async_call("switch", "turn_on", {"entity_id": home.entity_ids["vacation"]}, blocking=True)
            await entry.runtime_data.async_evaluate()
            assert home.profile == "vacation"
            assert entry.runtime_data.target == 17
            away_number = entry.runtime_data.entity_ids["away_temperature"]
            await hass.services.async_call("number", "set_value", {"entity_id": away_number, "value": 19.5}, blocking=True)
            assert entry.runtime_data.targets["away"] == 19.5
            hass.states.async_set("zone.home", "0", {"friendly_name": "Home", "latitude": 51, "longitude": 19, "radius": 100})
            for tracker in ("person.test_a", "device_tracker.test_b"):
                hass.states.async_set(tracker, "not_home", {})
            home_options = await hass.config_entries.options.async_init(household.entry_id)
            assert home_options["type"] == "form"
            assert home_options["step_id"] == "household"
            home_changed = await hass.config_entries.options.async_configure(home_options["flow_id"], {
                "presence_entities": ["person.test_a", "device_tracker.test_b"], "home_zone": "zone.home",
                "away_delay_minutes": 0, "prewarm_hours": 1,
            })
            assert home_changed["type"] == "create_entry"
            await hass.async_block_till_done()
            await hass.services.async_call("switch", "turn_off", {"entity_id": home.entity_ids["vacation"]}, blocking=True)
            await entry.runtime_data.async_evaluate()
            assert home.profile == "away"
            assert entry.runtime_data.target == 19.5
            await hass.services.async_call("switch", "turn_on", {"entity_id": home.entity_ids["coming_home"]}, blocking=True)
            await entry.runtime_data.async_evaluate()
            assert home.profile == "prewarming"
            assert home.vacation is False
            assert entry.runtime_data.target == 22
            assert entry.runtime_data.config["control_method"] == "pid"
            print(f"HA {importlib.metadata.version('homeassistant')}: room and household flows, PID metadata, profile numbers, presence, vacation/prewarm switches, frontend and settings reload passed.")
        finally:
            await hass.async_stop(force=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # This isolated host forbids OS adapter enumeration. An empty adapter
    # inventory is the only environment fixture; HA and our code remain real.
    with patch("ifaddr.get_adapters", return_value=[]):
        asyncio.run(main())

"""Validate supplied blueprints and exercise their triggers in isolated HA."""

from pathlib import Path


async def async_check_blueprints(hass, room_id, home):
    from homeassistant.components.automation.config import async_validate_config_item
    from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
    from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
    from homeassistant.core import callback
    from homeassistant.setup import async_setup_component
    from homeassistant.util import yaml

    received = []

    @callback
    def record(call):
        received.append(dict(call.data))

    hass.services.async_register("room_comfort_test", "record", record)
    hass.states.async_set("schedule.comfort_test", "off")
    hass.states.async_set("input_button.return_test", "unknown")
    hass.states.async_set("sensor.ready_test", "away", {"prewarm_ready": False})
    inputs = {
        "home_target_schedule": {"room": room_id, "schedule": "schedule.comfort_test",
                                 "target_mode": "cool", "active_temperature": 24.5, "inactive_temperature": 27},
        "coming_home_button": {"button": "input_button.return_test", "coming_home": home.entity_ids["coming_home"]},
        "coming_home_ready": {"home_mode": "sensor.ready_test", "ready_actions": [
            {"action": "room_comfort_test.record", "data": {"ready": True}}]},
        "room_mode_trigger": {"room": room_id, "mode": "cool", "start_triggers": [
            {"trigger": "event", "event_type": "test_choose_cooling"}]},
    }
    configs = []
    folder = Path(__file__).resolve().parents[1] / "blueprints/automation/room_comfort"
    for name, values in inputs.items():
        blueprint = Blueprint(yaml.load_yaml(str(folder / f"{name}.yaml")),
                              expected_domain="automation", schema=BLUEPRINT_SCHEMA)
        instance = BlueprintInputs(blueprint, {"id": f"test_{name}", "alias": f"Test {name}",
            "use_blueprint": {"path": f"room_comfort/{name}.yaml", "input": values}})
        instance.validate()
        config = instance.async_substitute()
        assert await async_validate_config_item(hass, "automation", config)
        configs.append(config)
    assert await async_setup_component(hass, "automation", {"automation": configs})
    await hass.async_start()
    await hass.async_block_till_done()
    assert len(hass.states.async_all("automation")) == 4

    room = next(e.runtime_data for e in hass.config_entries.async_entries("room_comfort")
                if e.data.get("kind") != "household")
    # Schedule writes only the cooling Home number, even during Vacation.
    await home.async_change("vacation", True)
    await room.async_change(mode="cool")
    hass.states.async_set("schedule.comfort_test", "on")
    await hass.async_block_till_done()
    assert room.cool_targets["home"] == 24.5
    assert room.cool_targets["vacation"] == 29
    assert room.targets["home"] == 22
    assert room.target == 29
    hass.states.async_set("schedule.comfort_test", "unavailable")
    await hass.async_block_till_done()
    assert room.cool_targets["home"] == 24.5
    hass.states.async_set("schedule.comfort_test", "off")
    await hass.async_block_till_done()
    assert room.cool_targets["home"] == 27
    assert room.enabled is False

    # Physical button state change starts Coming home and explicitly clears Vacation.
    hass.states.async_set("input_button.return_test", "2026-10-28T15:00:00+00:00")
    await hass.async_block_till_done()
    assert home.prewarming and not home.vacation
    assert room.enabled is False
    await home.async_change("coming_home", False)
    await room.async_evaluate()

    # Mode trigger changes the room, with no device-control opt-in side effect.
    await room.async_change(mode="heat")
    hass.bus.async_fire("test_choose_cooling")
    await hass.async_block_till_done()
    assert room.mode == "cool" and not room.enabled
    # Ready actions require both ready=True and the active return profile.
    hass.states.async_set("sensor.ready_test", "away", {"prewarm_ready": True})
    await hass.async_block_till_done()
    assert received == []
    hass.states.async_set("sensor.ready_test", "prewarming", {"prewarm_ready": False})
    await hass.async_block_till_done()
    hass.states.async_set("sensor.ready_test", "prewarming", {"prewarm_ready": True})
    await hass.async_block_till_done()
    assert received == [{"ready": True}]
    print("4 blueprints: HA schema/input validation, schedule/profile preservation, manual return button, mode trigger and ready actions passed.")

# Automations with Room Comfort

Use the room thermostat and Room Comfort entities in automations. Direct commands
to a managed radiator or AC will be overwritten while room control is enabled.
Blueprints provide a form in Home Assistant's automation editor; they do not start
anything until you create and enable an automation from them.

## Install the blueprints

The repository is public, so you can import each blueprint directly from its GitHub URL.
Open the import links below, choose your HA instance, and confirm the import.

| Blueprint | Import |
| --- | --- |
| Scheduled Home temperature | [Import into HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fqmciaq%2Fha-room-comfort%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Froom_comfort%2Fhome_target_schedule.yaml) |
| Coming-home button | [Import into HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fqmciaq%2Fha-room-comfort%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Froom_comfort%2Fcoming_home_button.yaml) |
| Notify when home is ready | [Import into HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fqmciaq%2Fha-room-comfort%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Froom_comfort%2Fcoming_home_ready.yaml) |
| Room mode from a trigger | [Import into HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fqmciaq%2Fha-room-comfort%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Froom_comfort%2Froom_mode_trigger.yaml) |

Alternatively, paste the GitHub file URL into HA's **Import blueprint** dialog.
For manual installation, copy `blueprints/automation/room_comfort/` into
`/config/blueprints/automation/room_comfort/`. The manual install ZIP includes it.
HACS integration installation does not copy these automation blueprints.

Open **Settings → Automations & scenes → Blueprints**, reload blueprints if needed,
then choose **Create automation** beside a Room Comfort blueprint. The Room Comfort
home panel also has an **Automations & blueprints** shortcut.

| Blueprint | Select in its form | Result |
| --- | --- | --- |
| Scheduled Home temperature | Room, Schedule helper, Heat/Cool target, two temperatures | Updates only the Home target when the schedule changes. Away and Vacation targets remain intact. |
| Coming-home button | Input button helper, shared Coming home comfort switch | A manual button press starts preparing enabled rooms and clears Vacation. |
| Notify when home is ready | Shared Home mode sensor, notification/action sequence | Runs selected actions when all enabled rooms are ready during Coming home. |
| Choose room mode from a trigger | Room, Heat/Cool/Off, triggers | Sets the room HVAC mode using the active profile's matching temperature. |

## Examples

- **Winter day/night:** create a Schedule helper for 07:00–22:00, then a scheduled
  Home temperature automation for Salon → Heating, active 21°C / inactive 19°C.
- **Summer:** create another for Salon → Cooling, active 24°C / inactive 27°C.
  Select Cool on the room or use the room-mode blueprint. Scheduling a cooling
  target alone does not switch on cooling.
- **Returning with your dog at home:** keep the configured Away heating/cooling
  limits, set each room's **For my return** mode, and press Coming home. You can
  use the shared switch directly on a dashboard; the button blueprint is optional.
- **Ready notification:** select your mobile app's `notify.mobile_app_…` action
  and a message such as “The rooms are at their Home targets.” The blueprint can
  notify again if temperatures drift and then become ready again.

The scheduler owns the selected Home target at each schedule transition and on
startup. Manual edits last until the next transition. It does not restore a
previous manual target when disabled. Values are Celsius even on a Fahrenheit
dashboard. All supplied blueprints preserve the live-control opt-in; preview-only
rooms remain preview-only.

## Native entities and actions

Entity IDs depend on your room names. Find them on the integration device page or
in the room thermostat's attributes (`heating_profile_temperature_entities`,
`cooling_profile_temperature_entities`, `coming_home_mode_entity`,
`household_entities`, `control_switch`). Existing heating number unique IDs remain
unchanged after upgrading.

| Task | Entity/action |
| --- | --- |
| Choose heating or cooling now | Room `climate.set_hvac_mode` (`heat`, `cool`, `off`) |
| Change active profile's target | Room `climate.set_temperature` |
| Edit a specific profile target | Corresponding `number.set_value` |
| Choose Heat/Cool for the next return | Per-room `select.select_option` (`heat` or `cool`) |
| Start/cancel coming home | Shared Coming home comfort `switch.turn_on` / `switch.turn_off` |
| Manually start/end vacation | Shared Vacation switch |
| Enable/disable automatic Away | Shared Automatic away switch |
| AC heating boost | Room `climate.set_preset_mode` with `boost` |

Presence and Vacation are already handled by the integration. You do not need a
second presence automation, and none of these blueprints starts Vacation
automatically. Heat and Cool are explicit modes; there is no automatic seasonal
changeover. Coming home uses each room's selected return mode until it ends.
Cooling uses hysteresis and the AC off-time guard; radiator PID applies to heating.

Outdoor limits and delayed door/window protection apply to all blueprints. Room
presence pauses apply to ordinary heating/cooling; explicitly starting Coming home
bypasses empty-room timers so it can prepare an empty house. It still obeys
outdoor/window restrictions and the live-control opt-in.

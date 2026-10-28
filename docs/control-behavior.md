# Room Comfort control behaviour — 0.4.0

## Radiator PID

The room sensor is the reference. PID runs in heating mode; it does not simply
open every radiator fully and turn it Off at the target. Its output is calculated
demand in the range 0–1. The UI displays that as heat demand %, never valve opening.

Defaults: Kp 0.3, Ki 0.006, Kd 0.1, holding bias 0.4, temperature deadband 0.1°C,
output hysteresis 0.03, and minimum TRV target-update interval 120 seconds. Time
constants use minutes. The holding bias accounts for a TRV needing some demand at
the room target rather than falling to zero power. Integral growth freezes in the
deadband; derivative is filtered and acts on the measurement, not setpoint changes.
Anti-windup rejects further integration into saturation. Demand slews up at most
0.15/minute and down at most 0.35/minute. A long downtime is not integrated.

Climate entities generally control targets, not physical valve positions. Each
head is set to its own local temperature plus an offset from −2°C to +3°C,
according to PID demand, rounded to the target step and clamped to its allowed
range. Missing local readings fall back to the room sensor. Native Heat remains
selected when idling near target. This lets the head's own regulator modulate.
No measured valve-position control is implied, and no repeated full/off PWM is used.

A legacy hysteresis controller can be explicitly selected instead. It retains
the old maximum-target/Off behaviour. PID state resets on room mode/profile
changes, new targets and sensor failures. Gain tuning still needs real equipment.

## Household modes

A single Home modes integration entry is created alongside the first room. It
owns native switches for Vacation, Coming home comfort and Automatic away, plus a
Home mode sensor. Its options select person/device_tracker entities, a geographic
HA home zone, an Away confirmation delay and a prewarm timeout.

All selected trackers must be known outside that zone before Away activates.
Unknown/unavailable, missing zone data, uncertain GPS or no selected trackers
preserve Home comfort. Zone membership uses HA's in_zones metadata when available,
Home/not_home for home trackers, and geographic coordinates with GPS uncertainty
for custom zones. One selected tracker inside prevents automatic Away.

Vacation is explicitly manual. It survives presence changes and restart until
disabled or until Coming home is started. Starting Vacation cancels prewarm.
Starting prewarm clears Vacation, applies Home targets and switches enabled room
controllers to their selected Heat or Cool return mode. Control-disabled rooms never begin operating hardware.

Prewarm remains active after reaching target, displaying Ready and maintaining
the Home targets. It ends on a new confirmed arrival, explicit cancellation or
the configured timeout. Its absolute deadline survives restart. Defaults are
five minutes of confirmed absence and a four-hour prewarm timeout.

Per-room Home, Away and Vacation heating targets default to 21°C, 19°C and 17°C;
separate cooling targets default to 24°C, 27°C and 29°C. They are
editable on cards, in room settings and through ordinary number entities. Moving
the main thermostat target edits the currently active profile. Prewarm uses Home.
The selected HVAC mode chooses its matching target bank. Off remains Off during
ordinary presence/profile changes. Explicit Coming home switches enabled rooms to
their selected return mode and keeps that mode afterward. Ready means at least
Home heat target minus 0.2°C in Heat, or at most Home cool target plus 0.2°C in Cool.
Cooling uses hysteresis and the AC cooldown guard, while PID controls radiators.
Changing the return mode during Coming home immediately applies it to enabled rooms.

## AC, faults and shutdown

AC heat boost is an explicit, bounded assist. It ends at the room target or its
timeout, then radiators maintain temperature. Prewarm does not implicitly start
AC boost. Cooling requires every radiator to report Off first. AC mode reversal
requires an observed Off state and at least 180 seconds of off time by default.

A room sensor that is invalid, unavailable, non-finite or stale requests reachable
outputs Off. A selected window contact that is open or unavailable does the same.
Boost is cancelled on those faults. Ordinary control resumes after recovery.

An assigned AC that is unavailable blocks radiator heating: its cooling state
cannot be confirmed stopped. To use radiators independently while repairing an
AC connection, unassign the optional AC in room options. A disconnected physical
device cannot be forced Off; device errors stay visible. HA-reported states are
the available confirmation, not independent physical proof of operation.

Turning Control devices off requests all outputs Off and keeps retrying failed
stops with a visible stopping status. Unloading makes a best-effort stop and
flushes persisted targets before a settings reload. Room target/mode/control
state survive restart; a one-shot AC boost never resumes automatically.

Competing native schedules/HA automations should not change assigned devices.
Turning the room Off, confirming physical devices Off, disabling Control devices,
and removing its integration entry reverses ownership. Old device schedules or
targets are not restored automatically. Shared multi-split restrictions and
central-boiler operation are outside this integration.


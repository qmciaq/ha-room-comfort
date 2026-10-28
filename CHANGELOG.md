# Changelog

## 0.5.0

- Public HACS custom-repository installation, badges, dashboard examples and support documentation.
- Global outdoor sensor and heating/cooling thresholds, per-room overrides or opt-out, hysteresis and stale-reading handling.
- Door/window opening debounce, with a default continuous-open delay of 10 seconds; unknown contacts still pause immediately.
- Room occupancy sensors with independent heating and cooling absence timers. Manual Coming home bypasses occupancy pauses; windows and outdoor gates still apply.
- Compact room controls and status tiles, with visual editors and grid examples.
- Public blueprint imports and a CI frontend-dependency fix.

Upgrading: outdoor control starts disabled. Existing windows now use the default
10-second delay unless configured otherwise; choose zero for immediate pause.
Room presence restrictions apply only after you select sensors. Review room
presence settings for pet comfort. All existing heating/cooling targets are kept.

## 0.4.0

- Separate Home/Away/Vacation cooling targets and a Heat/Cool coming-home selector.
- Cool remains visible with setup guidance when AC is not assigned.
- Four automation blueprints and dashboard shortcuts.

## 0.3.0

- PID radiator control with bounded native TRV target trimming.
- Household presence, Away/Vacation targets and manual Coming home controls.

# Validation — 0.4.0

- 82 Python PID/presence/household/controller tests passed locally.
- 25 Playwright tests passed in a real headless browser, using the production
  frontend and simulated HA state/service objects.
- Desktop (1440px), mobile (390px), dark theme and Polish labels were rendered.
- Browser checks cover room discovery, temperature adjustments, heat/cool/off,
  boost start/cancel/countdown, observe-only control, unavailable devices and
  sensor data, command errors, device more-info events, filters/search, HTML
  escaping, visual card editor events, and empty/missing-room states.
- New cooling checks cover independent target banks, combined mode/target calls,
  cooling return readiness, radiator interlocks, persistence and observe-only behaviour.
- All four blueprints pass actual HA blueprint input/schema and automation validation,
  plus triggered actions for schedule changes, manual return, mode selection and readiness.
- Offline distribution checks cover manifest fields, a single integration,
  local brand icon, source/JSON syntax, and version consistency.
- New checks cover partial PID output, deadband/noise behaviour, anti-windup,
  warm-up demand dropping at target, command rate limiting, sensor fail-safe,
  zone uncertainty, all-outside gating, manual Vacation, prewarm readiness,
  arrival/timeout/cancellation and profile restoration.
- An illustrative four-hour thermal model settled within 0.2°C of target while
  using partial demand. This is a synthetic model, not an equipment accuracy claim.
- A real isolated **HA Core 2026.10.4** load passed: UI setup and options flows,
  entity platforms, complete frontend entity links, sidebar registration,
  HTTP serving of the bundled JavaScript, room temperature/mode services in
  observe-only mode, and settings reload with target/mode preserved.
  Physical devices were simulated HA states. OS network-adapter enumeration
  was replaced with an empty inventory because that host operation is restricted;
  HA Core and the integration otherwise ran as installed packages.

The live HA installation has not been changed. Actual TRV/AC responses,
sensor calibration, competing schedules and shared multi-split restrictions
still need verification. The salon AC was unavailable when inspected.

Workflows being present does not mean GitHub Actions, Hassfest or HACS validation
have already passed. Those results must be checked after publishing the source.


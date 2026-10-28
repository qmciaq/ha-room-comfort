# Shared contribution rules

These rules are shared by coding agents and human contributors. The root
`AGENTS.md` and `CONTRIBUTING.md` both reference this file.

## Scope and structure

- Implement the requested behaviour and keep changes focused. Follow the user's
  requested GitHub workflow; otherwise use a branch and pull request describing
  the resulting behaviour, configuration changes and relevant validation.
- Keep every runtime dependency and bundled frontend file inside
  `custom_components/room_comfort/`. Maintain one integration per repository.
- Keep reusable automation blueprints in `blueprints/automation/room_comfort/`.
  They are imported separately from the integration. Preserve existing inputs
  where possible and document changes users must make.
- `dev/index.html` is a simulated-device preview. Production frontend code lives
  in `custom_components/room_comfort/frontend/room-comfort.js`. Regenerate the
  standalone `preview.html` and relevant screenshots when changing that UI.
- Preserve existing entity unique IDs and stored settings during upgrades.
  For a versioned release, keep the manifest, Python/frontend version constants,
  package metadata, resource examples and changelog consistent. Do not bump the
  integration version for documentation-only changes.

## Room control

- Preserve the explicit live-control opt-in. Observe-only rooms send no commands.
- Preserve confirmed-Off ordering before cooling and AC mode reversal, as well as
  the minimum AC off interval. A target-only command must not revive an opposite
  mode. Device failures must remain visible.
- Retain sensor freshness/unit checks, outdoor gates, delayed contact protection,
  independent room-absence timers and proper shutdown/reload behaviour.
- Unknown household/room presence does not count as confirmed absence. Unknown
  window state pauses control immediately. An enabled outdoor policy with invalid
  or stale readings pauses outputs.
- Manual Coming home bypasses empty-room pauses while active; it still obeys
  windows, outdoor limits, device interlocks and live-control opt-in.
- PID output is calculated heating demand. Native TRV setpoint trimming is not
  direct valve-position control. Do not claim measured output or hardware accuracy
  from a simulation.
- Keep HA I/O asynchronous, serialize controller mutations, and cancel listeners,
  pending callbacks and timers on unload. Flush persisted settings before reload.
- Use simulated devices or isolated HA for validation. Operate live household
  devices only when the user has instructed those actions.

## Frontend

- Keep the bundled cards dependency-free and use the integration's ordinary HA
  entities/services. Full, compact and status layouts must agree about room state.
- Support keyboard interaction, visible focus, narrow dashboard grids, light/dark
  themes and English/Polish labels.
- Escape entity names, attributes and service errors before inserting HTML.
- Show unavailable states and service failures clearly. Preserve focused controls
  during live updates and distinguish requested demand from physical output.

## Validation and review

Run checks appropriate to the change:

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
npm run check
npm test
```

For runtime/platform/configuration-flow changes, also run
`python scripts/smoke_ha.py` under the supported HA/Python environment described in
the README. This uses an isolated HA instance and simulated devices.

Controller changes should exercise mode transitions, failure handling,
observe-only behaviour and the relevant window/outdoor/presence interactions.
Frontend changes should check the affected user flow in a real browser. For
documentation-only changes, check references and `git diff --check`; a full
runtime/browser suite is unnecessary.

Describe what changed, why, what was verified and any material limitations. Inspect
actual GitHub check results before claiming HACS/hassfest or CI success. Do not
silence failed checks to present an update as passing.

## Documentation and contributions

- Update user-facing configuration examples and the changelog when behaviour or
  upgrade steps change. Describe the final behaviour without conversational history.
- Keep credentials, tokens, real tracker coordinates and private device snapshots
  out of code, examples, logs and screenshots.
- Do not claim acceptance into HACS's default catalog unless it has happened.
- Keep the owner's license choice explicit. Do not apply or change a license just
  because the repository is public or a license has been recommended.

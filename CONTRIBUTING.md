# Contributing

Use a branch and open a pull request describing the resulting behaviour, any
configuration changes, and how you tested it. Keep all runtime files inside
`custom_components/room_comfort/`; the bundled cards require no external build.

Run the checks listed in the README. Changes to device control should exercise
sensor failure, mode transitions, observe-only behaviour, windows, outdoor gates
and room presence. UI changes should check keyboard controls, narrow grids,
light/dark themes, translation and escaping of entity text.

Use simulated devices or an isolated HA instance for development. Changes must
preserve the room live-control opt-in and confirmed-off ordering before cooling.
Do not include credentials, real tracker coordinates or personal device snapshots.

Blueprints are separately imported by users. Keep their inputs compatible where
possible and document any action users need to take in the changelog.

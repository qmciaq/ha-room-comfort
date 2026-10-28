# HACS publication checks

This public repository has the single-integration layout, manifest, bundled
frontend, local brand assets, README rendering and HACS/hassfest workflows.
It has not been submitted to the HACS default catalog.

The repository owner still needs to complete GitHub metadata and choose a license:

- **About description:** `Room temperature control for Home Assistant: radiator PID, AC heating/cooling, presence profiles and dashboard cards.`
- **Suggested topics:** `home-assistant`, `hacs`, `custom-integration`, `climate`, `thermostat`, `pid`, `lovelace`.
- **License:** choose an OSI-approved license appropriate for how you want others to use the project, and add its exact LICENSE file. Public visibility alone does not grant an open-source license. No license has been chosen on your behalf.

These were missing when the repository became public. HACS validation reports
them as publication issues; its checks are intentionally not disabled or ignored.
The connected GitHub editing tools used for source changes do not expose the
repository About description/topics settings.

After the full validation workflow passes, publish a versioned GitHub release
matching the integration manifest. HACS custom repositories can use a default
branch without releases, but catalog inclusion requires additional review and a
release. Do not describe the integration as part of HACS's default catalog until
it has actually been accepted.

References: [HACS general requirements](https://www.hacs.xyz/docs/publish/start/),
[validation action](https://www.hacs.xyz/docs/publish/action/), and
[catalog inclusion](https://www.hacs.xyz/docs/publish/include/).

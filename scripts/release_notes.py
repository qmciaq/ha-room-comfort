"""Generate release notes for the manifest version, refusing missing changelog entries."""

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def release_notes(root: Path = ROOT):
    version = json.loads((root / "custom_components/room_comfort/manifest.json").read_text())["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Stable releases require a major.minor.patch manifest version")
    changelog = (root / "CHANGELOG.md").read_text()
    match = re.search(rf"^## {re.escape(version)}\s*\n(.*?)(?=^## |\Z)", changelog, re.M | re.S)
    if not match or not match.group(1).strip():
        raise ValueError(f"No changelog entry for {version}")
    return f"""{match.group(1).strip()}

### Installation

- Requires Home Assistant 2026.10.0 or newer.
- In HACS, add `qmciaq/ha-room-comfort` as a custom Integration repository and select `v{version}`.
- For manual installation, extract `room-comfort-{version}-install.zip` into your HA configuration directory. It includes the integration and optional blueprint files.
- Restart Home Assistant and refresh your browser after updating.
- If you previously installed a commit/default-branch build, use HACS Redownload once to select this named version if no update is offered.

New rooms start in observe-only mode. Review temperatures, sensor assignments and device states before enabling live control. Real equipment tuning is still required; automated validation uses simulated devices.

Licensed under MIT. [Interactive demo](https://qmciaq.github.io/ha-room-comfort/) · [Documentation](https://github.com/qmciaq/ha-room-comfort#readme)
"""


if __name__ == "__main__":
    print(release_notes())

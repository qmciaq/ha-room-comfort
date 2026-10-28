"""Offline distribution checks. Does not claim HACS/Core runtime validation."""

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components/room_comfort"
manifest = json.loads((INTEGRATION / "manifest.json").read_text())
hacs = json.loads((ROOT / "hacs.json").read_text())
assert [p.name for p in (ROOT / "custom_components").iterdir() if p.is_dir() and p.name != "__pycache__"] == ["room_comfort"]
for key in ("domain", "name", "documentation", "issue_tracker", "codeowners", "version"):
    assert manifest.get(key), f"Missing manifest field: {key}"
assert manifest["domain"] == "room_comfort"
assert manifest["config_flow"] is True
assert "panel_custom" in manifest["dependencies"]
assert hacs["name"] == manifest["name"]
assert (ROOT / "LICENSE").read_bytes() == (INTEGRATION / "LICENSE").read_bytes()
assert "MIT License" in (ROOT / "LICENSE").read_text()
assert (INTEGRATION / "brand/icon.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
for file in (ROOT / "custom_components").rglob("*.py"):
    ast.parse(file.read_text(), filename=str(file))
for file in ROOT.rglob("*.json"):
    if "node_modules" not in file.parts:
        json.loads(file.read_text())
frontend = (INTEGRATION / "frontend/room-comfort.js").read_text()
assert f'const VERSION = "{manifest["version"]}"' in frontend
assert f'VERSION = "{manifest["version"]}"' in (INTEGRATION / "const.py").read_text()
for component in ("room-comfort-card", "room-comfort-overview", "room-comfort-panel", "room-comfort-card-editor"):
    assert component in frontend
assert "ha-energy-meter" not in frontend
print(f"Distribution checks passed for Room Comfort {manifest['version']}")


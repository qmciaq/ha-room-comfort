"""Build an installable integration ZIP and a complete source ZIP."""

import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
version = json.loads((ROOT / "custom_components/room_comfort/manifest.json").read_text())["version"]
dest = ROOT / "dist"
dest.mkdir(exist_ok=True)
excluded = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "test-results", "playwright-report"}
files = [p for p in ROOT.rglob("*") if p.is_file() and not excluded.intersection(p.relative_to(ROOT).parts) and p.suffix != ".pyc"]
for name, selected in [
    (f"room-comfort-{version}-install.zip", [p for p in files if p.is_relative_to(ROOT / "custom_components")]),
    (f"room-comfort-{version}-source.zip", files),
]:
    with ZipFile(dest / name, "w", ZIP_DEFLATED) as archive:
        for p in sorted(selected):
            archive.write(p, p.relative_to(ROOT))
    with ZipFile(dest / name) as archive:
        assert archive.testzip() is None
    print(dest / name)

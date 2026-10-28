"""Build a portable static demo from the development page and production cards."""

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_TAG = '<script src="/custom_components/room_comfort/frontend/room-comfort.js"></script>'


def build(output: Path, standalone: bool = False):
    source = (ROOT / "dev/index.html").read_text()
    frontend = ROOT / "custom_components/room_comfort/frontend/room-comfort.js"
    if source.count(SCRIPT_TAG) != 1:
        raise ValueError("The demo must reference exactly one production card bundle")
    assets = output / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(frontend, assets / "room-comfort.js")
    (output / "index.html").write_text(source.replace(SCRIPT_TAG, '<script src="./assets/room-comfort.js"></script>'))
    (output / ".nojekyll").write_text("")
    if standalone:
        script = frontend.read_text().replace("</script", "<\\/script")
        (ROOT / "preview.html").write_text(source.replace(SCRIPT_TAG, f"<script>{script}</script>"))
    print(output.resolve())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/demo")
    parser.add_argument("--standalone", action="store_true", help="Also regenerate preview.html")
    args = parser.parse_args()
    build(args.output, args.standalone)

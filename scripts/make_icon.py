"""Render the app logo into a macOS .icns file (used when building the .app).

usage: python scripts/make_icon.py OUT.icns
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from PySide6.QtGui import QGuiApplication  # noqa: E402

from ui.components.logo_mark import logo_pixmap  # noqa: E402

# macOS icon grid: the artwork fills ~80% of the canvas, leaving room for the Dock shadow.
MARGIN_FRACTION = 0.1


def main():
    out = Path(sys.argv[1]).resolve()
    app = QGuiApplication([])  # noqa: F841  (QPixmap needs an application object)
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "icon.iconset"
        iconset.mkdir()
        for points in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                suffix = "" if scale == 1 else "@2x"
                logo_pixmap(points * scale, MARGIN_FRACTION).save(
                    str(iconset / f"icon_{points}x{points}{suffix}.png"))
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(out)], check=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

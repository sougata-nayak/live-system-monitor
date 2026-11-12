"""Build a double-clickable macOS app: dist/System Monitor.app

usage (from the project root, after `pip install -r requirements-dev.txt`):
    venv/bin/python scripts/build_app.py

Compiles with Nuitka (needs Xcode Command Line Tools for clang). The first build
takes a few minutes; later ones reuse Nuitka's cache.

The compile happens in ~/Library/Caches, not in the project: this project lives in
~/Desktop, which iCloud ("Desktop & Documents") syncs, and the metadata iCloud
attaches to files there makes `codesign` refuse to sign the app. Only the finished
app is copied to dist/.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = Path.home() / "Library" / "Caches" / "system-monitor-build"  # outside iCloud, see above
DIST = ROOT / "dist"
APP_NAME = "System Monitor"


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    icon = BUILD / "icon.icns"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_icon.py"), str(icon)], check=True)

    subprocess.run([
        sys.executable, "-m", "nuitka", str(ROOT / "src" / "main.py"),
        "--standalone",
        "--macos-create-app-bundle",
        f"--macos-app-name={APP_NAME}",
        f"--macos-app-icon={icon}",
        f"--output-filename={APP_NAME}",
        f"--output-dir={BUILD / 'nuitka'}",
        "--enable-plugin=pyside6",
        # pyqtgraph imports this with importlib at runtime, which Nuitka can't see.
        "--include-module=PySide6.QtOpenGL",
        "--noinclude-qt-translations",
        "--assume-yes-for-downloads",
        "--quiet",
    ], check=True, cwd=BUILD)

    built = BUILD / "nuitka" / "main.app"
    target = DIST / f"{APP_NAME}.app"
    DIST.mkdir(exist_ok=True)
    shutil.rmtree(target, ignore_errors=True)
    # ditto keeps the bundle's symlinks and code signature intact.
    subprocess.run(["ditto", str(built), str(target)], check=True)
    print(f"built {target}")


if __name__ == "__main__":
    main()

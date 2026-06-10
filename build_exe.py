import PyInstaller.__main__
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "src"
DIST = ROOT / "dist"
BUILD = ROOT / "build"

DIST.mkdir(parents=True, exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)

PyInstaller.__main__.run([
    str(ROOT / "main.py"),
    "--onefile",
    "--console",
    "--name", "loopforge",
    "--paths", str(SRC),
    "--distpath", str(DIST),
    "--workpath", str(BUILD / "pyinstaller"),
    "--specpath", str(BUILD),
    "--clean",
    "--noconfirm",
])

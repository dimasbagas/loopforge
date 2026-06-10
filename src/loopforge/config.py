from pathlib import Path
from typing import Optional

import sys

def _get_project_root() -> Path:
    """
    Deteksi project root secara otomatis:
    - Jika compiled (.exe via PyInstaller): gunakan folder di samping .exe
    - Jika Python script biasa: gunakan project root (3 level up dari config.py)
    """
    if getattr(sys, "frozen", False):
        # Sedang berjalan sebagai .exe (PyInstaller)
        return Path(sys.executable).resolve().parent
    else:
        # Sedang berjalan sebagai Python script
        return Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = _get_project_root()
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DOWNLOAD_DIR = PROJECT_ROOT / "downloads"
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_FILE = LOGS_DIR / "app.log"

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".webm", ".flv", ".wmv", ".m4v"}

DURATION_PRESETS = {
    "1h": 3600,
    "2h": 7200,
    "8h": 28800,
    "12h": 43200,
    "24h": 86400,
}

DEFAULT_QUALITY = "1080p"
FFMPEG_DEFAULT_THREADS = 0

class GPUInfo:
    available: bool = False
    name: Optional[str] = None
    encoder: str = "libx264"

    def __init__(self):
        self._detect()

    def _detect(self):
        import subprocess
        import shutil

        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                result = subprocess.run(
                    [nvidia_smi, "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=10, check=True
                )
                gpu_name = result.stdout.strip()
                if gpu_name:
                    self.available = True
                    self.name = gpu_name
                    self.encoder = "h264_nvenc"
                    return
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

        try:
            result = subprocess.run(
                ["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=15
            )
            if "h264_nvenc" in result.stdout:
                self.available = True
                self.name = "NVIDIA GPU (via FFmpeg)"
                self.encoder = "h264_nvenc"
                return
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        self.available = False
        self.name = None
        self.encoder = "libx264"


GPU = GPUInfo()

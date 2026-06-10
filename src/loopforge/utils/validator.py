from pathlib import Path
from ..config import SUPPORTED_VIDEO_EXTENSIONS


class ValidationError(Exception):
    pass


def validate_file_exists(path: str) -> Path:
    file_path = Path(path).resolve()
    if not file_path.exists():
        raise ValidationError(f"File tidak ditemukan: {path}")
    if not file_path.is_file():
        raise ValidationError(f"Path bukan file: {path}")
    return file_path


def validate_video_extension(path: Path) -> str:
    ext = path.suffix.lower()
    if ext not in SUPPORTED_VIDEO_EXTENSIONS:
        exts = ", ".join(sorted(SUPPORTED_VIDEO_EXTENSIONS))
        raise ValidationError(
            f"Format video tidak didukung: {ext}. "
            f"Format yang didukung: {exts}"
        )
    return ext


def validate_youtube_url(url: str) -> bool:
    import re
    patterns = [
        r"^https?://(?:www\.)?youtube\.com/watch\?v=.+",
        r"^https?://(?:www\.)?youtu\.be/.+",
        r"^https?://(?:www\.)?youtube\.com/embed/.+",
        r"^https?://(?:www\.)?youtube\.com/shorts/.+",
    ]
    return any(re.match(p, url) for p in patterns)


def validate_duration_positive(duration: float) -> float:
    if duration <= 0:
        raise ValidationError("Durasi harus lebih dari 0 detik")
    if duration > 86400 * 7:
        raise ValidationError("Durasi maksimal adalah 7 hari (604800 detik)")
    return duration


def validate_file_size(path: Path, max_gb: float = 50.0) -> int:
    size_bytes = path.stat().st_size
    size_gb = size_bytes / (1024 ** 3)
    if size_gb > max_gb:
        raise ValidationError(
            f"Ukuran file ({size_gb:.1f} GB) melebihi batas maksimal ({max_gb} GB)"
        )
    return size_bytes


def validate_ffmpeg_available() -> str:
    import shutil
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValidationError(
            "FFmpeg tidak ditemukan. Install FFmpeg terlebih dahulu:\n"
            "  Windows: winget install FFmpeg\n"
            "  macOS: brew install ffmpeg\n"
            "  Linux: sudo apt install ffmpeg"
        )
    return ffmpeg


def validate_ffprobe_available() -> str:
    import shutil
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise ValidationError(
            "FFprobe tidak ditemukan. Install FFmpeg terlebih dahulu:\n"
            "  Windows: winget install FFmpeg\n"
            "  macOS: brew install ffmpeg\n"
            "  Linux: sudo apt install ffmpeg"
        )
    return ffprobe


def validate_ytdlp_available() -> str:
    import shutil
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        raise ValidationError(
            "yt-dlp tidak ditemukan. Install yt-dlp terlebih dahulu:\n"
            "  pip install yt-dlp"
        )
    return yt_dlp


def check_disk_space(path: Path, required_bytes: int) -> None:
    try:
        import shutil
        usage = shutil.disk_usage(path.anchor if path.is_absolute() else path)
        if usage.free < required_bytes:
            from ..utils.logger import get_logger
            logger = get_logger()
            logger.warning(
                f"Peringatan: Ruang disk tersisa {usage.free / (1024**3):.1f} GB, "
                f"estimasi kebutuhan {required_bytes / (1024**3):.1f} GB"
            )
    except Exception:
        pass

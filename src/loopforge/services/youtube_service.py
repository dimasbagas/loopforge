import subprocess
import re
import shutil
import os
from pathlib import Path
from typing import Optional, Callable

from ..utils.logger import get_logger
from ..config import DOWNLOAD_DIR


class YouTubeError(Exception):
    pass


def _get_ytdlp_path() -> str:
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        try:
            import yt_dlp
            return "yt-dlp"
        except ImportError:
            raise YouTubeError(
                "yt-dlp tidak ditemukan. Install dengan: pip install yt-dlp"
            )
    return yt_dlp


def validate_youtube_url(url: str) -> bool:
    patterns = [
        r"^https?://(?:www\.)?youtube\.com/watch\?v=.+",
        r"^https?://(?:www\.)?youtu\.be/.+",
        r"^https?://(?:www\.)?youtube\.com/embed/.+",
        r"^https?://(?:www\.)?youtube\.com/shorts/.+",
    ]
    return any(re.match(p, url) for p in patterns)


def get_video_title(url: str) -> str:
    import yt_dlp
    logger = get_logger()

    try:
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("title", "unknown_video")
    except Exception as e:
        logger.debug(f"Gagal mendapatkan judul video: {e}")
        return "unknown_video"


def get_video_duration(url: str) -> float:
    import yt_dlp

    try:
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration = info.get("duration", 0)
            if duration is None:
                return 0.0
            return float(duration)
    except Exception as e:
        raise YouTubeError(f"Gagal mendapatkan durasi video: {str(e)}")


def download_video(
    url: str,
    output_dir: Optional[Path] = None,
    on_progress: Optional[Callable] = None,
) -> str:
    import yt_dlp
    logger = get_logger()

    output_dir = output_dir or DOWNLOAD_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    def progress_hook(d):
        if d.get("status") == "downloading":
            if on_progress:
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                if total > 0:
                    progress = min(downloaded / total, 1.0)
                    speed = d.get("speed", 0)
                    on_progress(progress, downloaded, total, speed)

    try:
        output_template = str(output_dir / "%(title).100s_%(id)s.%(ext)s")

        ydl_opts = {
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "outtmpl": output_template,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "ignoreerrors": False,
            "merge_output_format": "mp4",
            "postprocessors": [{
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            possible_exts = [".mp4", ".mkv", ".webm"]
            for ext in possible_exts:
                test_path = str(output_dir / f"{Path(filename).stem}{ext}")
                if Path(test_path).exists():
                    return test_path

            for f in output_dir.iterdir():
                if f.suffix in {".mp4", ".mkv", ".webm"}:
                    return str(f)

            return str(output_dir / f"{Path(filename).stem}.mp4")

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "HTTP Error 403" in error_msg:
            raise YouTubeError("Akses ditolak oleh YouTube (403). Coba URL lain atau gunakan cookie browser.")
        elif "Video unavailable" in error_msg:
            raise YouTubeError("Video tidak tersedia atau telah dihapus.")
        elif "Private video" in error_msg:
            raise YouTubeError("Video ini bersifat private.")
        elif "Age confirmation" in error_msg or "age-gate" in error_msg:
            raise YouTubeError("Video memerlukan konfirmasi usia. Gunakan --cookies-from-browser.")
        raise YouTubeError(f"Gagal mendownload video: {error_msg[:200]}")
    except Exception as e:
        raise YouTubeError(f"Gagal mendownload video: {str(e)[:200]}")

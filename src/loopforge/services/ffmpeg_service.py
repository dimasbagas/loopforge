import subprocess
import json
import shutil
import os
import signal
import threading
from pathlib import Path
from typing import Optional, Callable

from ..utils.logger import get_logger
from ..utils.validator import check_disk_space
from .gpu_service import get_encoder_flags


class FFmpegError(Exception):
    pass


class FFprobeError(Exception):
    pass


def _get_ffmpeg_path() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise FFmpegError("FFmpeg tidak ditemukan. Install FFmpeg terlebih dahulu.")
    return ffmpeg


def _get_ffprobe_path() -> str:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise FFprobeError("FFprobe tidak ditemukan. Install FFmpeg terlebih dahulu.")
    return ffprobe


def get_video_info(file_path: str) -> dict:
    ffprobe = _get_ffprobe_path()
    logger = get_logger()

    try:
        result = subprocess.run(
            [
                ffprobe, "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", file_path,
            ],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            raise FFprobeError(f"Gagal membaca informasi video: {result.stderr.strip()}")

        data = json.loads(result.stdout)

        video_stream = None
        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and video_stream is None:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and audio_stream is None:
                audio_stream = stream

        if not video_stream:
            raise FFprobeError("Tidak ada stream video dalam file")

        format_info = data.get("format", {})
        duration = float(format_info.get("duration", 0))
        size_bytes = int(format_info.get("size", 0))

        width = video_stream.get("width", 0)
        height = video_stream.get("height", 0)

        fps_str = video_stream.get("r_frame_rate", "0/1")
        if "/" in fps_str:
            try:
                num, den = fps_str.split("/")
                fps = float(num) / float(den) if float(den) > 0 else 0
            except (ValueError, ZeroDivisionError):
                fps = 0.0
        else:
            fps = float(fps_str) if fps_str else 0.0

        codec = video_stream.get("codec_name", "unknown")
        bitrate = format_info.get("bit_rate", "0")

        if bitrate and bitrate != "0":
            bitrate_val = int(bitrate) // 1000
            bitrate_str = f"{bitrate_val} kbps"
        else:
            bitrate_str = "N/A"

        file_size_mb = size_bytes / (1024 * 1024)
        if file_size_mb > 1024:
            file_size_str = f"{file_size_mb / 1024:.2f} GB"
        else:
            file_size_str = f"{file_size_mb:.2f} MB"

        return {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "resolution": f"{width}x{height}",
            "width": width,
            "height": height,
            "fps": fps,
            "codec": codec,
            "duration": duration,
            "bitrate": bitrate_str,
            "file_size": file_size_str,
            "file_size_bytes": size_bytes,
            "has_audio": audio_stream is not None,
        }

    except json.JSONDecodeError:
        raise FFprobeError("Gagal menguraikan output FFprobe")
    except subprocess.TimeoutExpired:
        raise FFprobeError("FFprobe timeout saat membaca video")
    except FileNotFoundError:
        raise FFprobeError("FFprobe tidak ditemukan")


def estimate_output_size(video_info: dict, target_duration: float) -> float:
    duration = video_info.get("duration", 0)
    file_size_bytes = video_info.get("file_size_bytes", 0)
    if duration <= 0 or file_size_bytes <= 0:
        return 0
    ratio = target_duration / duration
    estimated_bytes = file_size_bytes * ratio
    return estimated_bytes / (1024 * 1024)


def estimate_render_time(source_duration: float, target_duration: float, has_gpu: bool) -> str:
    ratio = target_duration / max(source_duration, 1)
    if has_gpu:
        seconds = ratio * 0.15
    else:
        seconds = ratio * 0.5
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours}j {minutes}m {secs}d"
    elif minutes > 0:
        return f"{minutes}m {secs}d"
    return f"{secs}d"


def render_loop(
    input_path: str,
    output_path: str,
    target_duration: float,
    encoder_flags: list[str],
    on_progress: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> str:
    ffmpeg = _get_ffmpeg_path()
    logger = get_logger()

    video_info = get_video_info(input_path)
    check_disk_space(Path(output_path).parent, int(video_info.get("file_size_bytes", 0) * (target_duration / max(video_info["duration"], 1))))

    has_audio = video_info["has_audio"]
    source_duration = video_info["duration"]
    codec = video_info.get("codec", "").lower()

    # Gunakan concat demuxer untuk AV1/VP9 demi kompatibilitas
    use_concat = False
    if codec in ["av1", "vp9", "libdav1d", "libaom-av1", "libvpx-vp9"]:
        use_concat = True
        logger.info(f"Codec {codec} terdeteksi, menggunakan concat demuxer...")

    # Dapatkan encoder flags dengan mempertimbangkan source codec
    encoder_flags = get_encoder_flags(codec)

    if use_concat:
        return _render_loop_concat(
            input_path=input_path,
            output_path=output_path,
            target_duration=target_duration,
            encoder_flags=encoder_flags,
            source_codec=codec,
            has_audio=has_audio,
            source_duration=source_duration,
            on_progress=on_progress,
            cancel_check=cancel_check,
        )

    # Konversi path ke format yang aman untuk FFmpeg di Windows
    safe_input_path = str(Path(input_path).resolve()).replace("\\", "/")

    cmd = [ffmpeg, "-y"]
    cmd.extend(["-stream_loop", "-1", "-i", safe_input_path])
    cmd.extend(["-t", str(target_duration)])
    cmd.extend(encoder_flags)

    if has_audio:
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    else:
        cmd.extend(["-an"])

    cmd.extend(["-progress", "pipe:1"])
    cmd.append(output_path)

    logger.debug(f"FFmpeg command: {' '.join(cmd)}")

    return _run_ffmpeg_with_progress(
        cmd, target_duration, on_progress, cancel_check, logger
    )


def _render_loop_concat(
    input_path: str,
    output_path: str,
    target_duration: float,
    encoder_flags: list[str],
    source_codec: Optional[str] = None,
    has_audio: bool = True,
    source_duration: float = 0,
    on_progress: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> str:
    """Render loop menggunakan concat demuxer — kompatibel dengan AV1/VP9."""
    import tempfile
    ffmpeg = _get_ffmpeg_path()
    logger = get_logger()

    loops_needed = int(target_duration / max(source_duration, 1)) + 2

    # Buat concat list file sementara
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        concat_file = f.name
        for _ in range(loops_needed):
            # Windows path: ganti backslash dan escape single quote
            safe_path = input_path.replace("\\", "/").replace("'", "\\'")
            f.write(f"file '{safe_path}'\n")

    try:
        cmd = [ffmpeg, "-y"]
        cmd.extend(["-f", "concat", "-safe", "0", "-i", concat_file])
        cmd.extend(["-t", str(target_duration)])
        cmd.extend(encoder_flags)

        if has_audio:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-an"])

        cmd.extend(["-progress", "pipe:1"])
        cmd.append(output_path)

        logger.debug(f"FFmpeg concat command: {' '.join(cmd)}")

        return _run_ffmpeg_with_progress(
            cmd, target_duration, on_progress, cancel_check, logger
        )
    finally:
        try:
            os.unlink(concat_file)
        except Exception:
            pass


def _run_ffmpeg_with_progress(
    cmd: list,
    target_duration: float,
    on_progress: Optional[Callable],
    cancel_check: Optional[Callable],
    logger,
) -> str:
    """Jalankan perintah FFmpeg dan baca progress dari stdout (pipe:1)."""
    output_path = cmd[-1]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # Pisahkan stderr agar bisa dibaca untuk error reporting
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        encoding="utf-8",
        errors="replace",
    )

    stderr_lines = []

    def read_stderr():
        try:
            for line in iter(process.stderr.readline, ""):
                if line:
                    stderr_lines.append(line.strip())
        except Exception:
            pass

    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_thread.start()

    try:
        for line in iter(process.stdout.readline, ""):
            line = line.strip()
            if not line:
                continue

            # Log progress lines in debug mode for easier troubleshooting
            logger.debug(f"FFmpeg progress: {line}")

            if line.startswith("out_time_us="):
                try:
                    val = line.split("=", 1)[1].strip()
                    if val and val != "N/A":
                        time_us = int(val)
                        if time_us >= 0:
                            current_time = time_us / 1_000_000
                            if on_progress and target_duration > 0:
                                on_progress(
                                    min(current_time / target_duration, 1.0),
                                    current_time,
                                )
                except (ValueError, IndexError):
                    pass
            elif line.startswith("out_time="):
                # Fallback jika out_time_us tidak ada atau bermasalah
                try:
                    val = line.split("=", 1)[1].strip()
                    if val and val != "N/A" and ":" in val:
                        # Format HH:MM:SS.mmmmmm
                        h, m, s = val.split(":")
                        current_time = int(h) * 3600 + int(m) * 60 + float(s)
                        if on_progress and target_duration > 0:
                            on_progress(
                                min(current_time / target_duration, 1.0),
                                current_time,
                            )
                except (ValueError, IndexError):
                    pass

            elif line.startswith("progress=end"):
                if on_progress:
                    on_progress(1.0, target_duration)

            if cancel_check and cancel_check():
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise FFmpegError("Render dibatalkan oleh pengguna")

        # Debug print the last few lines of stderr if any
        if stderr_lines:
            for ln in stderr_lines[-10:]:
                logger.debug(f"FFmpeg stderr: {ln}")

        process.wait()

        if process.returncode != 0:
            error_msg = "\n".join(stderr_lines[-5:]) if stderr_lines else "Unknown error"
            logger.error(f"FFmpeg error (code {process.returncode}): {error_msg}")
            if "nvenc" in error_msg.lower() or "nvidia" in error_msg.lower():
                raise FFmpegError("GPU encoder gagal. Coba tanpa GPU atau update driver NVIDIA.")
            raise FFmpegError(f"FFmpeg gagal (code {process.returncode}): {error_msg[:300]}")

    except FFmpegError:
        raise
    except Exception as e:
        try:
            process.terminate()
        except Exception:
            pass
        raise FFmpegError(f"Error saat render: {str(e)}")
    finally:
        try:
            process.stdout.close()
        except Exception:
            pass
        try:
            process.stderr.close()
        except Exception:
            pass

    return output_path


def copy_stream_loop(
    input_path: str,
    output_path: str,
    target_duration: float,
) -> str:
    ffmpeg = _get_ffmpeg_path()
    logger = get_logger()

    cmd = [ffmpeg, "-y"]
    cmd.extend(["-stream_loop", "-1", "-i", input_path])
    cmd.extend(["-t", str(target_duration)])
    cmd.extend(["-c", "copy"])
    cmd.append(output_path)

    logger.debug(f"FFmpeg copy command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=3600,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if result.returncode != 0:
            raise FFmpegError(f"Fast loop gagal: {result.stderr.strip()[:200]}")
        return output_path
    except subprocess.TimeoutExpired:
        raise FFmpegError("Fast loop timeout")
    except FileNotFoundError:
        raise FFmpegError("FFmpeg tidak ditemukan")


def analyze_seamless(input_path: str) -> float:
    try:
        import cv2
        import numpy as np

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            return 0.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames < 2:
            cap.release()
            return 0.0

        first_frame = None
        last_frame = None

        ret, first_frame = cap.read()
        if not ret:
            cap.release()
            return 0.0

        first_frame = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
        first_frame = cv2.resize(first_frame, (320, 240))

        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, last_frame = cap.read()
        if not ret:
            cap.release()
            return 0.0

        last_frame = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
        last_frame = cv2.resize(last_frame, (320, 240))

        diff = cv2.absdiff(first_frame, last_frame)
        mse = np.mean(diff ** 2)
        max_mse = 255.0 ** 2
        similarity = max(0, 1 - (mse / max_mse))
        score = round(similarity * 100, 1)

        cap.release()
        return score

    except ImportError:
        return 0.0
    except Exception:
        return 0.0

from typing import Optional
from ..config import GPU


def get_gpu_info() -> dict:
    return {
        "available": GPU.available,
        "name": GPU.name,
        "encoder": GPU.encoder,
    }


def get_encoder() -> str:
    return GPU.encoder


def is_gpu_available() -> bool:
    return GPU.available


def get_gpu_name() -> str:
    return GPU.name or "CPU"


def get_encoder_flags(source_codec: Optional[str] = None) -> list[str]:
    # Jika source adalah AV1, NVENC terkadang gagal (Function not implemented)
    # Gunakan CPU encoder sebagai fallback yang lebih aman
    if source_codec and source_codec.lower() in ["av1", "libdav1d", "libaom-av1"]:
        return [
            "-c:v", "libx264", "-preset", "medium",
            "-crf", "23", "-threads", "0",
        ]

    if GPU.available:
        return ["-c:v", "h264_nvenc", "-preset", "p7", "-rc", "vbr", "-cq", "23"]
    return [
        "-c:v", "libx264", "-preset", "medium",
        "-crf", "23", "-threads", "0",
    ]

from typing import Optional

try:
    from pydantic import BaseModel
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def model_dump(self):
            return self.__dict__

        def dict(self):
            return self.__dict__


class VideoInfo(BaseModel):
    file_path: str = ""
    file_name: str = ""
    resolution: str = ""
    fps: float = 0.0
    codec: str = ""
    duration: float = 0.0
    bitrate: str = ""
    file_size: str = ""


class LoopResult(BaseModel):
    source_file: str = ""
    source_duration: float = 0.0
    target_duration: float = 0.0
    total_loops: int = 0
    encoder: str = ""
    output_file: str = ""
    seamless_score: Optional[float] = None
    gpu_name: Optional[str] = None
    estimated_size_mb: Optional[float] = None
    estimated_render_time: Optional[str] = None


class BatchResult(BaseModel):
    total_files: int = 0
    successful: int = 0
    failed: int = 0
    results: list[LoopResult] = []

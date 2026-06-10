from pydantic import BaseModel
from typing import Optional


class VideoInfo(BaseModel):
    file_path: str
    file_name: str
    resolution: str
    fps: float
    codec: str
    duration: float
    bitrate: str
    file_size: str


class LoopResult(BaseModel):
    source_file: str
    source_duration: float
    target_duration: float
    total_loops: int
    encoder: str
    output_file: str
    seamless_score: Optional[float] = None
    gpu_name: Optional[str] = None
    estimated_size_mb: Optional[float] = None
    estimated_render_time: Optional[str] = None


class BatchResult(BaseModel):
    total_files: int
    successful: int
    failed: int
    results: list[LoopResult]

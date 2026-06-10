import json
from pathlib import Path
from typing import Optional

from ..models import LoopResult
from .duration_service import format_duration


def generate_metadata(result: LoopResult, output_dir: Path) -> str:
    metadata = {
        "source_file": result.source_file,
        "source_duration": format_duration(result.source_duration),
        "target_duration": format_duration(result.target_duration),
        "total_loops": result.total_loops,
        "encoder": result.encoder,
        "gpu_name": result.gpu_name,
        "output_file": result.output_file,
        "estimated_size_mb": round(result.estimated_size_mb, 2) if result.estimated_size_mb else None,
        "seamless_score": result.seamless_score,
    }

    output_path = Path(result.output_file)
    metadata_file = output_dir / f"{output_path.stem}_metadata.json"

    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return str(metadata_file)


def load_metadata(metadata_file: str) -> Optional[dict]:
    path = Path(metadata_file)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

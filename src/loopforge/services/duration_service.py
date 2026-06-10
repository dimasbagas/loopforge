import re
from typing import Union


class DurationParseError(Exception):
    pass


_DURATION_PATTERNS = [
    (r"^(\d+)h$", lambda m: int(m.group(1)) * 3600),
    (r"^(\d+)m$", lambda m: int(m.group(1)) * 60),
    (r"^(\d+)s$", lambda m: int(m.group(1))),
    (r"^(\d+):(\d+):(\d+)$", lambda m: (
        int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    )),
    (r"^(\d+):(\d+)$", lambda m: (
        int(m.group(1)) * 60 + int(m.group(2))
    )),
]


def parse_duration(value: Union[str, int, float]) -> float:
    if isinstance(value, (int, float)):
        return float(value)

    value = value.strip().lower()

    for pattern, handler in _DURATION_PATTERNS:
        match = re.match(pattern, value)
        if match:
            result = handler(match)
            return float(result)

    try:
        return float(value)
    except ValueError:
        raise DurationParseError(
            f"Format durasi tidak valid: '{value}'. "
            f"Gunakan format seperti: 1h, 90m, 3600s, 01:30:00, atau angka dalam detik"
        )


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_loops(source_duration: float, target_duration: float) -> int:
    if source_duration <= 0:
        raise DurationParseError("Durasi sumber harus lebih dari 0 detik")
    loops = int(target_duration / source_duration)
    if target_duration % source_duration != 0:
        loops += 1
    return loops


def get_duration_presets() -> dict:
    from ..config import DURATION_PRESETS
    return dict(DURATION_PRESETS)

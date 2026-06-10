import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from ..config import LOGS_DIR, LOGS_FILE


def setup_logger(name: str = "loopforge", debug: bool = False) -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if logger.handlers:
        logger.handlers.clear()

    rich_handler = RichHandler(
        rich_tracebacks=True,
        show_time=False,
        show_path=False,
        omit_repeated_times=False,
    )
    rich_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    rich_fmt = logging.Formatter("%(message)s")
    rich_handler.setFormatter(rich_fmt)
    logger.addHandler(rich_handler)

    file_handler = logging.FileHandler(
        str(LOGS_FILE), mode="a", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "loopforge") -> logging.Logger:
    return logging.getLogger(name)

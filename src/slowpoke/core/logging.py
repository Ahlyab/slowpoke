from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(level: str, log_file: Path, dev_mode: bool = False) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    resolved_level = logging.DEBUG if dev_mode else getattr(logging, level, logging.INFO)
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

from config import LoggingConfig


def setup_logging(cfg: LoggingConfig) -> None:
    level = getattr(logging, str(cfg.level).upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    # Ensure log directory exists
    log_path = Path(cfg.file_path)
    if log_path.parent and not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Clear existing handlers to avoid duplicates
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path), maxBytes=int(cfg.max_bytes), backupCount=int(cfg.backup_count), encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    root.addHandler(file_handler)

    if cfg.console:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        console.setLevel(level)
        root.addHandler(console)

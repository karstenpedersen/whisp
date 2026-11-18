import logging
from pathlib import Path

from rich.logging import RichHandler

log = logging.getLogger("whisper")


def setup_logging(level: int = logging.INFO, log_file: Path | None = None) -> None:
    handlers: list[logging.Handler] = [
        RichHandler(
            show_path=False,
            log_time_format="%Y-%m-%d %H:%M:%S",
        )
    ]
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-7s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        handlers.append(file_handler)

    log.handlers = handlers
    log.setLevel(level)
    log.propagate = False

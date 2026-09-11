import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_PATH = os.path.join(os.path.dirname(__file__), "app.log")
_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return

    root = logging.getLogger("travel_agent")
    root.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    file_handler = RotatingFileHandler(_LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root.addHandler(file_handler)
    root.addHandler(console_handler)
    root.propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Returns a namespaced logger under 'travel_agent.*' writing to app.log + console."""
    _configure()
    return logging.getLogger(f"travel_agent.{name}")

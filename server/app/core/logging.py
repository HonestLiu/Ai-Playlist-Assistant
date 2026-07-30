"""日志配置。入口只调用一次 ``configure_logging()``。"""

from __future__ import annotations

import logging
from logging.config import dictConfig

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                    "datefmt": "%H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                }
            },
            "loggers": {
                "app": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn.error": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn.access": {"handlers": ["console"], "level": "WARNING", "propagate": False},
                "httpx": {"handlers": ["console"], "level": "WARNING", "propagate": False},
            },
            "root": {"handlers": ["console"], "level": level},
        }
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """统一从 ``app.`` 命名空间取 logger。"""

    return logging.getLogger(name if name.startswith("app") else f"app.{name}")

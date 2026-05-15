"""Configured application logger."""

import logging
import sys
from typing import TYPE_CHECKING

from loguru import logger as _logger

from app.settings import settings

if TYPE_CHECKING:
    from loguru import Logger


class InterceptHandler(logging.Handler):
    def emit(self, record):  # type: ignore[no-untyped-def]
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logger() -> "Logger":
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    _logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": logging.DEBUG if settings.debug else logging.INFO,
            }
        ],
    )

    return _logger


logger = setup_logger()

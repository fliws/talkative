from __future__ import annotations

import os
from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    logger.remove()
    # Log to stdout in structured format
    logger.add(lambda msg: print(msg, end=""), level=level, serialize=True, backtrace=False, diagnose=False)


def get_logger():
    return logger

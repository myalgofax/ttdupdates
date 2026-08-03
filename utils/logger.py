from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logger(level: str = "INFO", rotation: str = "10 MB", retention: str = "30 days") -> None:
    logger.remove()

    logger.add(sys.stdout, level=level, colorize=True,
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>")

    logger.add(LOGS_DIR / "application.log", level=level, rotation=rotation,
               retention=retention, encoding="utf-8",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}")

    logger.add(LOGS_DIR / "error.log", level="ERROR", rotation=rotation,
               retention=retention, encoding="utf-8",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}")

    logger.add(LOGS_DIR / "browser.log", level="DEBUG", rotation=rotation,
               retention=retention, encoding="utf-8", filter="browser",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")

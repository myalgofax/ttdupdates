from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from loguru import logger

from config.settings import load_config
from services.database_service import DatabaseService
from services.news_monitor import NewsMonitor
from services.notification_service import NotificationService
from services.scheduler_service import SchedulerService
from utils.logger import setup_logger

BASE_DIR = Path(__file__).resolve().parent


async def cmd_monitor_news():
    config = load_config()
    setup_logger(config.logging.level, config.logging.rotation, config.logging.retention)
    db = DatabaseService(str(BASE_DIR / config.database.path))
    notifications = NotificationService(config, db)
    news = NewsMonitor(config, db, notifications)
    scheduler = SchedulerService(config)
    scheduler.add_news_monitor(news.check)
    scheduler.start()
    logger.info("News monitor running. Press Ctrl+C to stop.")
    try:
        await news.check()
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Stopping news monitor")
    finally:
        scheduler.stop()


COMMANDS = {
    "monitor-news": cmd_monitor_news,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python app.py <command>\nCommands: {', '.join(COMMANDS)}")
        sys.exit(1)
    asyncio.run(COMMANDS[sys.argv[1]]())


if __name__ == "__main__":
    main()

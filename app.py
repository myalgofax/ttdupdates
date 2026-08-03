from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from loguru import logger

from config.settings import load_config
from models.events import Event, EventType
from services.auth_service import AuthService, SessionService
from services.browser_service import BrowserService
from services.database_service import DatabaseService
from services.monitor_service import MonitorService
from services.news_monitor import NewsMonitor
from services.notification_service import NotificationService
from services.scheduler_service import SchedulerService
from services.screenshot_service import ScreenshotService
from utils.logger import setup_logger

BASE_DIR = Path(__file__).resolve().parent


def _build_news_services():
    config = load_config()
    setup_logger(config.logging.level, config.logging.rotation, config.logging.retention)
    db = DatabaseService(str(BASE_DIR / config.database.path))
    notifications = NotificationService(config, db)
    news = NewsMonitor(config, db, notifications)
    scheduler = SchedulerService(config)
    return config, db, notifications, news, scheduler


def _build_services():
    config = load_config()
    setup_logger(config.logging.level, config.logging.rotation, config.logging.retention)
    db = DatabaseService(str(BASE_DIR / config.database.path))
    browser = BrowserService(config)
    screenshots = ScreenshotService(db, str(BASE_DIR / "screenshots"))
    notifications = NotificationService(config, db)
    auth = AuthService(config, browser, db, screenshots)
    session = SessionService(config, browser, db, auth)
    monitor = MonitorService(config, browser, db, notifications, screenshots)
    news = NewsMonitor(config, db, notifications)
    scheduler = SchedulerService(config, screenshots)
    return config, db, browser, screenshots, notifications, auth, session, monitor, news, scheduler


async def cmd_login():
    config, db, browser, screenshots, notifications, auth, *_ = _build_services()
    await browser.start()
    try:
        success = await auth.login()
        if success:
            await notifications.notify("Login Success\n\nStatus: LOGGED IN")
        else:
            logger.error("Login failed")
    finally:
        await browser.stop()


async def cmd_validate_session():
    config, db, browser, screenshots, notifications, auth, session, *_ = _build_services()
    await browser.start()
    try:
        valid = await session.validate()
        logger.info(f"Session valid: {valid}")
    finally:
        await browser.stop()


async def cmd_screenshot():
    config, db, browser, screenshots, *_ = _build_services()
    await browser.start()
    try:
        page = await browser.new_page()
        await page.goto(config.urls.srivari_seva, wait_until="domcontentloaded")
        path = await screenshots.capture(page, "manual_screenshot")
        logger.info(f"Screenshot saved: {path}")
        await page.close()
    finally:
        await browser.stop()


async def cmd_monitor_booking():
    config, db, browser, screenshots, notifications, auth, session, monitor, news, scheduler = _build_services()
    await browser.start()
    await session.validate()
    scheduler.add_booking_monitor(monitor.check)
    scheduler.add_session_validator(session.validate)
    scheduler.add_cleanup()
    scheduler.start()
    logger.info("Booking monitor running. Press Ctrl+C to stop.")
    try:
        await monitor.check()  # immediate first check
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Stopping booking monitor")
    finally:
        scheduler.stop()
        await browser.stop()


async def cmd_monitor_news():
    _, _, _, news, scheduler = _build_news_services()
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


async def cmd_health():
    config, db, browser, screenshots, notifications, auth, session, *_ = _build_services()
    await browser.start()
    try:
        valid = await session.validate()
        status = "HEALTHY" if valid else "SESSION_EXPIRED"
        db.save_event(Event(event_type=EventType.HEALTH_CHECK, message=f"Health check: {status}"))
        await notifications.notify(f"Health Check\n\nStatus: {status}")
        logger.info(f"Health check: {status}")
    finally:
        await browser.stop()


COMMANDS = {
    "login": cmd_login,
    "validate-session": cmd_validate_session,
    "screenshot": cmd_screenshot,
    "monitor-booking": cmd_monitor_booking,
    "monitor-news": cmd_monitor_news,
    "health": cmd_health,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python app.py <command>\nCommands: {', '.join(COMMANDS)}")
        sys.exit(1)
    asyncio.run(COMMANDS[sys.argv[1]]())


if __name__ == "__main__":
    main()

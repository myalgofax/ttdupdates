from __future__ import annotations

import asyncio
from typing import Callable, Coroutine, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from config.settings import AppConfig
from services.screenshot_service import ScreenshotService


class SchedulerService:
    def __init__(self, config: AppConfig, screenshots: ScreenshotService | None = None) -> None:
        self._config = config
        self._screenshots = screenshots
        self._scheduler = AsyncIOScheduler()

    def _wrap(self, coro_fn: Callable[[], Coroutine[Any, Any, None]]) -> Callable:
        async def job():
            try:
                await coro_fn()
            except Exception as e:
                logger.error(f"Scheduled job error [{coro_fn.__name__}]: {e}")
        return job

    def add_booking_monitor(self, check_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        interval = self._config.polling.default_interval
        self._scheduler.add_job(self._wrap(check_fn), IntervalTrigger(seconds=interval), id="booking_monitor")
        logger.info(f"Booking monitor scheduled every {interval}s")

    def add_news_monitor(self, check_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._scheduler.add_job(self._wrap(check_fn), CronTrigger(hour=10, minute=0), id="news_monitor_am")
        self._scheduler.add_job(self._wrap(check_fn), CronTrigger(hour=14, minute=30), id="news_monitor_pm")
        logger.info("News monitor scheduled at 10:00 AM and 2:30 PM daily")

    def add_session_validator(self, validate_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._scheduler.add_job(self._wrap(validate_fn), IntervalTrigger(seconds=300), id="session_validator")
        logger.info("Session validator scheduled every 300s")

    def add_health_check(self, health_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        cfg = self._config.scheduler
        self._scheduler.add_job(
            self._wrap(health_fn),
            CronTrigger(hour=cfg.health_check_hour, minute=cfg.health_check_minute),
            id="health_check",
        )
        logger.info(f"Health check scheduled at {cfg.health_check_hour:02d}:{cfg.health_check_minute:02d}")

    def add_cleanup(self) -> None:
        if not self._screenshots:
            return
        cfg = self._config.scheduler

        async def cleanup():
            self._screenshots.cleanup_old(cfg.screenshot_retention_days)

        self._scheduler.add_job(
            self._wrap(cleanup),
            CronTrigger(hour=cfg.cleanup_hour, minute=cfg.cleanup_minute),
            id="cleanup",
        )
        logger.info("Cleanup job scheduled")

    def start(self) -> None:
        self._scheduler.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

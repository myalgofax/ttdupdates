from __future__ import annotations

from typing import Callable, Coroutine, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from config.settings import AppConfig


class SchedulerService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._scheduler = AsyncIOScheduler()

    def _wrap(self, coro_fn: Callable[[], Coroutine[Any, Any, None]]) -> Callable:
        async def job():
            try:
                await coro_fn()
            except Exception as e:
                logger.error(f"Scheduled job error [{coro_fn.__name__}]: {e}")
        return job

    def add_news_monitor(self, check_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        self._scheduler.add_job(self._wrap(check_fn), CronTrigger(hour=10, minute=0), id="news_monitor_am")
        self._scheduler.add_job(self._wrap(check_fn), CronTrigger(hour=14, minute=30), id="news_monitor_pm")
        logger.info("News monitor scheduled at 10:00 AM and 2:30 PM daily")

    def add_self_ping(self, url: str) -> None:
        async def ping():
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.get(url)
                logger.debug("Self ping OK")
            except Exception:
                pass
        self._scheduler.add_job(self._wrap(ping), CronTrigger(minute="*/10"), id="self_ping")
        logger.info("Self ping scheduled every 10 minutes")

    def start(self) -> None:
        self._scheduler.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

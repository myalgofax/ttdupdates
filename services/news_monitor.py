from __future__ import annotations

from datetime import datetime

import httpx
from loguru import logger

from config.settings import AppConfig
from models.events import Event, EventType, NewsItem
from services.database_service import DatabaseService
from services.notification_service import NotificationService


class NewsMonitor:
    def __init__(
        self,
        config: AppConfig,
        db: DatabaseService,
        notifications: NotificationService,
    ) -> None:
        self._config = config
        self._db = db
        self._notifications = notifications

    async def check(self) -> None:
        logger.info("Checking TTD news API")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    self._config.urls.news_api,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "application/json",
                        "Referer": "https://ttdevasthanams.ap.gov.in/",
                    }
                )
                resp.raise_for_status()
                data = resp.json()

            updates = data["data"][0]["attributes"]["update"]
            known_titles = self._db.get_all_news_titles()

            for item in updates:
                title = item.get("cta") or item.get("data", "")[:80]
                content = item.get("data", "")
                if not title:
                    continue
                if title in known_titles:
                    continue
                news = NewsItem(title=title, content=content, detected_at=datetime.utcnow())
                is_new = self._db.save_news(news)
                if is_new:
                    self._db.save_event(Event(
                        event_type=EventType.NEW_NOTIFICATION,
                        message=f"New TTD news: {title}",
                    ))
                    await self._notifications.notify(f"📰 New TTD News\n\n{title}\n\n{content[:300]}")
                    logger.info(f"New news item detected: {title}")

        except Exception as e:
            logger.error(f"News monitor error: {e}")
            try:
                self._db.save_event(Event(event_type=EventType.ERROR, message=str(e)))
            except Exception:
                pass

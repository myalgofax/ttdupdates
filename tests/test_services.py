from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from models.events import EventType


@pytest.mark.asyncio
async def test_monitor_detects_status_change(tmp_path):
    from services.monitor_service import MonitorService
    from config.settings import AppConfig, BrowserConfig, UrlsConfig, PollingConfig
    from config.settings import NotificationsConfig, LoggingConfig, DatabaseConfig, StorageConfig, SchedulerConfig

    config = AppConfig(
        browser=BrowserConfig(), notifications=NotificationsConfig(),
        logging=LoggingConfig(), database=DatabaseConfig(),
        storage=StorageConfig(), scheduler=SchedulerConfig(),
        polling=PollingConfig(),
        urls=UrlsConfig(base="http://x.com", login="http://x.com/login",
                        dashboard="http://x.com/dash", srivari_seva="http://x.com/seva",
                        news="http://x.com/news"),
    )

    db = MagicMock()
    db.save_event = MagicMock()
    notifications = MagicMock()
    notifications.notify = AsyncMock()
    screenshots = MagicMock()
    screenshots.capture = AsyncMock(return_value="/tmp/shot.png")
    browser = MagicMock()

    mock_page = AsyncMock()
    mock_page.inner_text = AsyncMock(return_value="Book Now - available")
    mock_page.close = AsyncMock()
    browser.new_page = AsyncMock(return_value=mock_page)

    with patch("services.monitor_service.SrivariPage") as MockSrivari:
        instance = AsyncMock()
        instance.open = AsyncMock()
        instance.get_booking_status = AsyncMock(return_value="AVAILABLE")
        instance.get_page_text = AsyncMock(return_value="book now available")
        MockSrivari.return_value = instance

        svc = MonitorService(config, browser, db, notifications, screenshots)
        await svc.check()

    notifications.notify.assert_called_once()
    db.save_event.assert_called_once()


@pytest.mark.asyncio
async def test_news_monitor_saves_new_item(tmp_path):
    from services.news_monitor import NewsMonitor
    from services.database_service import DatabaseService
    from config.settings import AppConfig, BrowserConfig, UrlsConfig, PollingConfig
    from config.settings import NotificationsConfig, LoggingConfig, DatabaseConfig, StorageConfig, SchedulerConfig

    config = AppConfig(
        browser=BrowserConfig(), notifications=NotificationsConfig(),
        logging=LoggingConfig(), database=DatabaseConfig(path=str(tmp_path / "db.db")),
        storage=StorageConfig(), scheduler=SchedulerConfig(),
        polling=PollingConfig(),
        urls=UrlsConfig(base="http://x.com", login="http://x.com/login",
                        dashboard="http://x.com/dash", srivari_seva="http://x.com/seva",
                        news="http://x.com/news"),
    )

    db = DatabaseService(str(tmp_path / "db.db"))
    notifications = MagicMock()
    notifications.notify = AsyncMock()
    screenshots = MagicMock()
    screenshots.capture = AsyncMock(return_value="/tmp/shot.png")
    browser = MagicMock()

    mock_page = AsyncMock()
    mock_page.close = AsyncMock()
    browser.new_page = AsyncMock(return_value=mock_page)

    with patch("services.news_monitor.NewsPage") as MockNews:
        instance = AsyncMock()
        instance.open = AsyncMock()
        instance.get_all_news_text = AsyncMock(return_value=[
            {"title": "General Srivari Seva booking open for October", "url": "http://x.com/news/1"}
        ])
        MockNews.return_value = instance

        monitor = NewsMonitor(config, browser, db, notifications, screenshots)
        await monitor.check()

    assert "General Srivari Seva booking open for October" in db.get_all_news_titles()
    notifications.notify.assert_called_once()

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from models.events import Event, EventType, NewsItem
from services.database_service import DatabaseService


@pytest.fixture
def db(tmp_path):
    return DatabaseService(str(tmp_path / "test.db"))


def test_save_and_retrieve_news(db):
    item = NewsItem(title="General Srivari Seva booking open", url="http://example.com", detected_at=datetime.utcnow())
    assert db.save_news(item) is True
    assert db.save_news(item) is False  # duplicate
    assert "General Srivari Seva booking open" in db.get_all_news_titles()


def test_save_event(db):
    event = Event(event_type=EventType.LOGIN_SUCCESS, message="Test login")
    row_id = db.save_event(event)
    assert row_id > 0


def test_save_screenshot(db):
    from models.events import ScreenshotRecord
    record = ScreenshotRecord(context="test", file_path="/tmp/test.png", created_at=datetime.utcnow())
    db.save_screenshot(record)
    old = db.get_old_screenshots(0)
    assert any("test.png" in p for p in old)

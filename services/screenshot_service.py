from __future__ import annotations

from datetime import datetime
from pathlib import Path

from loguru import logger
from playwright.async_api import Page

from services.database_service import DatabaseService
from models.events import ScreenshotRecord
from utils.helpers import timestamp_filename


class ScreenshotService:
    def __init__(self, db: DatabaseService, screenshots_dir: str = "screenshots") -> None:
        self._db = db
        self._dir = Path(screenshots_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    async def capture(self, page: Page, context: str) -> str:
        filename = timestamp_filename(context)
        path = self._dir / filename
        await page.screenshot(path=str(path), full_page=True)
        record = ScreenshotRecord(context=context, file_path=str(path), created_at=datetime.utcnow())
        self._db.save_screenshot(record)
        logger.info(f"Screenshot saved: {path}")
        return str(path)

    def cleanup_old(self, older_than_days: int) -> None:
        old_paths = self._db.get_old_screenshots(older_than_days)
        for p in old_paths:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"Could not delete screenshot {p}: {e}")
        self._db.delete_old_screenshots(older_than_days)
        logger.info(f"Cleaned up {len(old_paths)} old screenshots")

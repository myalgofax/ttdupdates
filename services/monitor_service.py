from __future__ import annotations

from loguru import logger

from config.settings import AppConfig
from models.events import Event, EventType
from pages.srivari_page import SrivariPage
from services.browser_service import BrowserService
from services.database_service import DatabaseService
from services.notification_service import NotificationService
from services.screenshot_service import ScreenshotService
from utils.constants import BOOKING_AVAILABLE, BOOKING_CLOSED


class MonitorService:
    def __init__(
        self,
        config: AppConfig,
        browser: BrowserService,
        db: DatabaseService,
        notifications: NotificationService,
        screenshots: ScreenshotService,
    ) -> None:
        self._config = config
        self._browser = browser
        self._db = db
        self._notifications = notifications
        self._screenshots = screenshots
        self._last_status: str = ""
        self._last_text_hash: str = ""

    async def check(self) -> None:
        logger.info("Checking Srivari Seva booking page")
        page = await self._browser.new_page()
        try:
            srivari = SrivariPage(page, self._config.urls.srivari_seva)
            await srivari.open()

            current_status = await srivari.get_booking_status()
            current_text = await srivari.get_page_text()
            current_hash = str(hash(current_text))

            status_changed = current_status != self._last_status
            page_changed = current_hash != self._last_text_hash and self._last_text_hash != ""

            if status_changed or page_changed:
                screenshot_path = await self._screenshots.capture(page, f"booking_{current_status.lower()}")

                if status_changed:
                    event_type = EventType.BOOKING_OPEN if current_status == BOOKING_AVAILABLE else (
                        EventType.BOOKING_CLOSED if current_status == BOOKING_CLOSED else EventType.WEBSITE_CHANGED
                    )
                    self._db.save_event(Event(
                        event_type=event_type,
                        message=f"Booking status changed: {self._last_status} → {current_status}",
                        screenshot_path=screenshot_path,
                    ))
                    await self._notifications.notify(
                        f"Booking Status Changed\n\nStatus: {current_status}",
                        screenshot_path=screenshot_path,
                    )
                    logger.info(f"Booking status changed: {self._last_status} → {current_status}")

                elif page_changed:
                    self._db.save_event(Event(
                        event_type=EventType.WEBSITE_CHANGED,
                        message="Booking page content changed",
                        screenshot_path=screenshot_path,
                    ))
                    await self._notifications.notify(
                        "Website Changed\n\nThe booking page content has changed.",
                        screenshot_path=screenshot_path,
                    )
                    logger.info("Booking page content changed")

                self._last_status = current_status
                self._last_text_hash = current_hash
            else:
                logger.debug(f"No change detected. Status: {current_status}")

        except Exception as e:
            logger.exception(f"Monitor error: {e}")
            self._db.save_event(Event(event_type=EventType.ERROR, message=f"Monitor error: {e}"))
        finally:
            await page.close()

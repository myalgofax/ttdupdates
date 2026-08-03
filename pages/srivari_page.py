from __future__ import annotations

from playwright.async_api import Page

from pages.base_page import BasePage
from utils.constants import BOOKING_AVAILABLE, BOOKING_CLOSED, BOOKING_UNKNOWN


class SrivariPage(BasePage):
    BOOK_BUTTON_SELECTOR = "a[href*='Booking'], button:has-text('Book'), a:has-text('Book Now')"
    AVAILABILITY_KEYWORDS_OPEN = ["book now", "available", "open", "proceed"]
    AVAILABILITY_KEYWORDS_CLOSED = ["closed", "not available", "no slots", "fully booked"]

    def __init__(self, page: Page, srivari_url: str) -> None:
        super().__init__(page)
        self._srivari_url = srivari_url

    async def open(self) -> None:
        await self.navigate(self._srivari_url)

    async def get_page_text(self) -> str:
        return (await self.page.inner_text("body")).lower()

    async def get_booking_status(self) -> str:
        text = await self.get_page_text()
        if any(kw in text for kw in self.AVAILABILITY_KEYWORDS_OPEN):
            return BOOKING_AVAILABLE
        if any(kw in text for kw in self.AVAILABILITY_KEYWORDS_CLOSED):
            return BOOKING_CLOSED
        return BOOKING_UNKNOWN

    async def is_book_button_visible(self) -> bool:
        try:
            await self.page.wait_for_selector(self.BOOK_BUTTON_SELECTOR, timeout=3000)
            return True
        except Exception:
            return False

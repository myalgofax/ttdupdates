from __future__ import annotations

from playwright.async_api import Page

from pages.base_page import BasePage
from utils.constants import NEWS_KEYWORDS


class NewsPage(BasePage):
    def __init__(self, page: Page, news_url: str) -> None:
        super().__init__(page)
        self._news_url = news_url

    async def open(self) -> None:
        await self.navigate(self._news_url)

    async def get_news_items(self) -> list[dict[str, str]]:
        """Extract news items as list of {title, url} dicts."""
        items: list[dict[str, str]] = []
        try:
            links = await self.page.query_selector_all("a")
            for link in links:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                if text and any(kw in text.lower() for kw in NEWS_KEYWORDS):
                    items.append({"title": text, "url": href})
        except Exception:
            pass
        return items

    async def get_all_news_text(self) -> list[dict[str, str]]:
        """Broader extraction — all visible news/announcement links."""
        items: list[dict[str, str]] = []
        try:
            # Try common news list selectors
            for selector in [".news-item", ".announcement", "li a", ".content a"]:
                links = await self.page.query_selector_all(selector)
                for link in links:
                    text = (await link.inner_text()).strip()
                    href = await link.get_attribute("href") or ""
                    if text and len(text) > 10:
                        items.append({"title": text, "url": href})
            if not items:
                items = await self.get_news_items()
        except Exception:
            pass
        return items

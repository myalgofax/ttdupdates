from __future__ import annotations

from playwright.async_api import Page


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    async def navigate(self, url: str) -> None:
        await self.page.goto(url, wait_until="domcontentloaded")

    async def get_title(self) -> str:
        return await self.page.title()

    async def get_url(self) -> str:
        return self.page.url

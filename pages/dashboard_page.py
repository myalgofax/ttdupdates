from __future__ import annotations

from playwright.async_api import Page

from pages.base_page import BasePage


class DashboardPage(BasePage):
    def __init__(self, page: Page, dashboard_url: str) -> None:
        super().__init__(page)
        self._dashboard_url = dashboard_url

    async def open(self) -> None:
        await self.navigate(self._dashboard_url)

    async def is_authenticated(self) -> bool:
        content = await self.page.content()
        return "logout" in content.lower() or "sign out" in content.lower()

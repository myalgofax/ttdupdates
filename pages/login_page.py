from __future__ import annotations

from playwright.async_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME_SELECTOR = "#UserName"
    PASSWORD_SELECTOR = "#Password"
    LOGIN_BUTTON_SELECTOR = "input[type='submit'], button[type='submit']"
    OTP_SELECTOR = "#OTP, input[name='OTP'], input[placeholder*='OTP'], input[placeholder*='otp']"

    def __init__(self, page: Page, login_url: str) -> None:
        super().__init__(page)
        self._login_url = login_url

    async def open(self) -> None:
        await self.navigate(self._login_url)

    async def fill_credentials(self, username: str, password: str) -> None:
        await self.page.fill(self.USERNAME_SELECTOR, username)
        await self.page.fill(self.PASSWORD_SELECTOR, password)

    async def click_login(self) -> None:
        await self.page.click(self.LOGIN_BUTTON_SELECTOR)
        await self.page.wait_for_load_state("domcontentloaded")

    async def is_otp_required(self) -> bool:
        try:
            await self.page.wait_for_selector(self.OTP_SELECTOR, timeout=5000)
            return True
        except Exception:
            return False

    async def fill_otp(self, otp: str) -> None:
        await self.page.fill(self.OTP_SELECTOR, otp)
        await self.page.click(self.LOGIN_BUTTON_SELECTOR)
        await self.page.wait_for_load_state("domcontentloaded")

    async def is_logged_in(self, dashboard_url: str) -> bool:
        return dashboard_url.rstrip("/") in self.page.url or "logout" in (await self.page.content()).lower()

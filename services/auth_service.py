from __future__ import annotations

from datetime import datetime

from loguru import logger

from config.settings import AppConfig
from models.events import Event, EventType, SessionRecord
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage
from services.browser_service import BrowserService
from services.database_service import DatabaseService
from services.screenshot_service import ScreenshotService


class AuthService:
    def __init__(
        self,
        config: AppConfig,
        browser: BrowserService,
        db: DatabaseService,
        screenshots: ScreenshotService,
    ) -> None:
        self._config = config
        self._browser = browser
        self._db = db
        self._screenshots = screenshots

    async def login(self) -> bool:
        logger.info("Starting login flow")
        page = await self._browser.new_page()
        login_page = LoginPage(page, self._config.urls.login)

        try:
            await login_page.open()
            await self._screenshots.capture(page, "login_page")
            await login_page.fill_credentials(self._config.username, self._config.password)
            await login_page.click_login()

            if await login_page.is_otp_required():
                logger.info("OTP page detected — waiting for user input")
                otp = input("\n🔐 Enter the OTP received on your phone: ").strip()
                await login_page.fill_otp(otp)

            if await login_page.is_logged_in(self._config.urls.dashboard):
                await self._browser.save_storage_state()
                await self._screenshots.capture(page, "login_success")
                self._db.save_event(Event(event_type=EventType.LOGIN_SUCCESS, message="Login successful"))
                self._db.save_session(SessionRecord(status="active", auth_path=self._config.storage.auth_path,
                                                    created_at=datetime.utcnow()))
                logger.info("Login successful")
                return True

            logger.error("Login failed — dashboard not reached")
            await self._screenshots.capture(page, "login_failed")
            return False

        except Exception as e:
            logger.exception(f"Login error: {e}")
            await self._screenshots.capture(page, "login_error")
            return False
        finally:
            await page.close()


class SessionService:
    def __init__(
        self,
        config: AppConfig,
        browser: BrowserService,
        db: DatabaseService,
        auth: AuthService,
    ) -> None:
        self._config = config
        self._browser = browser
        self._db = db
        self._auth = auth

    async def validate(self) -> bool:
        """Check if current session is still valid; re-login if not."""
        logger.info("Validating session")
        page = await self._browser.new_page()
        try:
            dashboard = DashboardPage(page, self._config.urls.dashboard)
            await dashboard.open()
            if await dashboard.is_authenticated():
                logger.info("Session is valid")
                return True

            logger.warning("Session expired — re-logging in")
            self._db.save_event(Event(event_type=EventType.SESSION_EXPIRED, message="Session expired, re-login required"))
            await page.close()
            return await self._auth.login()
        except Exception as e:
            logger.exception(f"Session validation error: {e}")
            return False
        finally:
            try:
                await page.close()
            except Exception:
                pass

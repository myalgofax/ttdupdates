from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from loguru import logger
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from config.settings import AppConfig
from utils.constants import MAX_BROWSER_RESTARTS


class BrowserService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._restart_count = 0

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        await self._launch_browser()
        logger.info("Browser started")

    async def _launch_browser(self) -> None:
        assert self._playwright is not None
        auth_path = Path(self._config.storage.auth_path)

        launch_kwargs = {
            "headless": self._config.browser.headless,
            "slow_mo": self._config.browser.slow_mo,
        }

        self._browser = await self._playwright.chromium.launch(**launch_kwargs)

        context_kwargs: dict = {
            "viewport": self._config.browser.viewport,
            "java_script_enabled": True,
        }

        if auth_path.exists():
            logger.info("Loading saved storage state")
            context_kwargs["storage_state"] = str(auth_path)

        self._context = await self._browser.new_context(**context_kwargs)
        self._context.set_default_timeout(self._config.browser.timeout)

    async def new_page(self) -> Page:
        if self._context is None:
            await self._launch_browser()
        assert self._context is not None
        return await self._context.new_page()

    async def save_storage_state(self) -> None:
        if self._context is None:
            return
        auth_path = Path(self._config.storage.auth_path)
        auth_path.parent.mkdir(parents=True, exist_ok=True)
        await self._context.storage_state(path=str(auth_path))

        # Also save cookies separately
        cookies = await self._context.cookies()
        cookies_path = Path(self._config.storage.cookies_path)
        cookies_path.write_text(json.dumps(cookies, indent=2))
        logger.info("Storage state and cookies saved")

    async def restart(self) -> None:
        if self._restart_count >= MAX_BROWSER_RESTARTS:
            logger.error("Max browser restarts reached")
            raise RuntimeError("Max browser restarts exceeded")
        self._restart_count += 1
        logger.warning(f"Restarting browser (attempt {self._restart_count})")
        await self.close()
        await self._launch_browser()
        logger.info("Browser restarted successfully")

    async def close(self) -> None:
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None

    async def stop(self) -> None:
        await self.close()
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser stopped")

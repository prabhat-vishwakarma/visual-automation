"""Browser session management (Playwright).

Responsibilities: start Playwright, launch/attach a browser, optionally use a
persistent profile, expose a Page, manage navigation timeouts, close cleanly.
"""

from __future__ import annotations

import time
from pathlib import Path

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from ..config import BrowserConfig
from ..exceptions import AuthenticationTimeout, BrowserSessionError
from ..telemetry.logger import get_logger

logger = get_logger(__name__)

AUTH_POLL_INTERVAL_SECONDS = 1.0


class BrowserSession:
    def __init__(self, config: BrowserConfig) -> None:
        self._config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self) -> None:
        """Launch the configured browser and attach to a page."""
        try:
            self._playwright = await async_playwright().start()
        except Exception as exc:
            raise BrowserSessionError(f"failed to start playwright: {exc}") from exc

        try:
            if self._config.headless:
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=self._config.launch_args,
                )
            else:
                self._browser = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self._profile_dir()),
                    headless=False,
                    args=self._config.launch_args,
                )
        except Exception as exc:
            raise BrowserSessionError(f"failed to launch browser: {exc}") from exc

        if self._config.headless:
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
        else:
            self._context = self._browser

        self._page = (
            self._context.pages[0]
            if self._context.pages
            else await self._context.new_page()
        )
        self.page.set_default_timeout(self._config.navigation_timeout_ms)
        logger.info(
            "browser_session_started",
            browser=self._config.browser,
            headless=self._config.headless,
        )

    def _profile_dir(self) -> Path:
        return Path(self._config.persistent_profile)

    @property
    def page(self) -> Page:
        if self._page is None:
            raise BrowserSessionError("browser session not started")
        return self._page

    async def get_page(self) -> Page:
        return self.page

    async def navigate(self, url: str) -> None:
        await self.page.goto(url, wait_until="domcontentloaded")
        logger.info("page_navigated", url=url)

    async def wait_until_authenticated(
        self,
        authenticated_selector: str,
        timeout_seconds: int,
    ) -> None:
        """Wait for a manual login to complete by polling a marker selector."""
        deadline = time.monotonic() + timeout_seconds
        while True:
            if await self._marker_visible(authenticated_selector):
                logger.info("authentication_detected")
                return
            if time.monotonic() > deadline:
                raise AuthenticationTimeout(
                    f"authenticated marker '{authenticated_selector}' not seen within "
                    f"{timeout_seconds}s"
                )
            await self.page.wait_for_timeout(500)

    async def _marker_visible(self, selector: str) -> bool:
        try:
            return await self.page.locator(selector).first.is_visible()
        except Exception:
            return False

    async def close(self) -> None:
        try:
            if self._browser is not None:
                await self._browser.close()
        except Exception:
            logger.warning("browser_close_error")
        if self._playwright is not None:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._page = None
        logger.info("browser_session_closed")
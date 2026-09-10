"""Result verification after submission.

The workflow must never assume a click means success. Outcomes:
    SUCCESS | REJECTED | TIMEOUT | UNEXPECTED_PAGE | BROWSER_ERROR
"""

from __future__ import annotations

from playwright.async_api import Page

from ..telemetry.logger import get_logger

logger = get_logger(__name__)


class ResultVerifier:
    def __init__(
        self,
        success_selector: str,
        rejection_selector: str | None,
        timeout_seconds: int,
        success_url: str | None = None,
    ) -> None:
        self.success_selector = success_selector
        self.rejection_selector = rejection_selector
        self.timeout_seconds = timeout_seconds
        self.success_url = success_url

    async def verify(self, page: Page) -> str:
        if await self._locator_visible(page, self.success_selector):
            return "success"

        if (
            self.rejection_selector
            and await self._locator_visible(page, self.rejection_selector)
        ):
            return "rejected"

        try:
            await page.locator(self.success_selector).first.wait_for(
                state="visible",
                timeout=self.timeout_seconds * 1000,
            )
            return "success"
        except Exception as exc:
            logger.debug("success_marker_missed", error=str(exc))

        if (
            self.rejection_selector
            and await self._locator_visible(page, self.rejection_selector)
        ):
            return "rejected"

        if self.success_url is not None and self.success_url in page.url:
            return "success"

        logger.warning("verification_timeout")
        return "timeout"

    @staticmethod
    async def _locator_visible(page: Page, selector: str) -> bool:
        try:
            return await page.locator(selector).first.is_visible()
        except Exception:
            return False
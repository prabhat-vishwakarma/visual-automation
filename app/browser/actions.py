"""Browser action layer: fill, confirm value, click exactly once."""

from __future__ import annotations

from playwright.async_api import Locator

from ..exceptions import InputNotFound, SubmissionError
from ..telemetry.logger import get_logger

logger = get_logger(__name__)


class BrowserActions:
    @staticmethod
    async def fill_text(locator: Locator, value: str) -> None:
        """Locate, ensure enabled/editable, clear, fill, and confirm the value."""
        try:
            await locator.wait_for(state="attached", timeout=10000)
            await locator.fill("")
            await locator.fill(value)
        except Exception as exc:
            raise InputNotFound(f"failed to fill input: {exc}") from exc

        confirmation = await locator.input_value()
        if confirmation != value:
            raise SubmissionError(
                f"input confirmation mismatch: expected {value!r}, got {confirmation!r}"
            )
        logger.info("field_filled", length=len(value))

    @staticmethod
    async def click(locator: Locator) -> None:
        """Click exactly once; no auto-retry here."""
        try:
            await locator.wait_for(state="visible", timeout=10000)
            await locator.click()
        except Exception as exc:
            raise SubmissionError(f"failed to click control: {exc}") from exc
        logger.info("control_clicked")
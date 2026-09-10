"""Navigation helpers with bounded retry."""

from __future__ import annotations

import asyncio

from playwright.async_api import Page

from ..config import WorkflowConfig
from ..exceptions import TargetNotFound
from ..telemetry.logger import get_logger

logger = get_logger(__name__)


async def wait_for_selector(
    page: Page,
    selector: str,
    timeout_seconds: int,
    description: str = "selector",
) -> None:
    """Wait for a selector to appear within a bounded timeout."""
    try:
        await page.locator(selector).first.wait_for(
            state="visible",
            timeout=timeout_seconds * 1000,
        )
    except Exception as exc:
        raise TargetNotFound(
            f"{description} '{selector}' not visible within {timeout_seconds}s"
        ) from exc
    logger.info("target_detected", target=description, selector=selector)


async def retry_navigation(page: Page, url: str, config: WorkflowConfig) -> None:
    """Navigate with bounded retries."""
    for attempt in range(1, config.navigation_retry_limit + 2):
        try:
            await page.goto(url, wait_until="domcontentloaded")
            return
        except Exception:
            if attempt > config.navigation_retry_limit:
                raise
            logger.warning("navigation_retry", attempt=attempt, url=url)
            await asyncio.sleep(1.0)
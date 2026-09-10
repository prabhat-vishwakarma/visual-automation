"""Screenshot capture manager.

Primary path: element screenshot (small crop, no region detection).
Secondary path: full-page screenshot fallback.
Normal successful runs keep images in memory; disk writes are reserved for
debug mode and failure artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from playwright.async_api import Locator, Page

from ..exceptions import ScreenshotError
from ..telemetry.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Screenshot:
    data: bytes
    width: int
    height: int
    captured_at: datetime
    source: str


class ScreenshotManager:
    async def capture_element(self, locator: Locator, timeout_ms: int = 10000) -> Screenshot:
        """Capture only the target image element."""
        try:
            await locator.wait_for(state="visible", timeout=timeout_ms)
            data = await locator.screenshot()
        except Exception as exc:
            raise ScreenshotError(f"element screenshot failed: {exc}") from exc

        width, height = await self._element_size(locator)
        logger.info("element_captured", width=width, height=height)
        return Screenshot(
            data=data,
            width=width,
            height=height,
            captured_at=utcnow(),
            source="element",
        )

    async def capture_page(self, page: Page) -> Screenshot:
        """Full-page screenshot fallback."""
        try:
            data = await page.screenshot(full_page=False)
        except Exception as exc:
            raise ScreenshotError(f"page screenshot failed: {exc}") from exc

        return Screenshot(
            data=data,
            width=0,
            height=0,
            captured_at=utcnow(),
            source="page",
        )

    @staticmethod
    def save_failure_artifact(run_id: str, root: str, name: str, image: bytes) -> None:
        from pathlib import Path

        target = Path(root) / "failures" / run_id
        target.mkdir(parents=True, exist_ok=True)
        (target / name).write_bytes(image)
        logger.info("failure_artifact_saved", run_id=run_id, name=name)

    @staticmethod
    async def _element_size(locator: Locator) -> tuple[int, int]:
        try:
            box = await locator.bounding_box()
            if box:
                return int(box["width"]), int(box["height"])
        except Exception as exc:
            logger.debug("bounding_box_unavailable", error=str(exc))
        return 0, 0


def utcnow() -> datetime:
    return datetime.now(UTC)
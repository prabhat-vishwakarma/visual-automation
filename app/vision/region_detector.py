"""Optional visual region detector.

DOM-based targeting is preferred whenever possible. This module is a thin
placeholder for a future lightweight detector (bounding-box crop) used only
when DOM selection is unreliable or unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.async_api import Page

from .image_utils import decode_image


@dataclass
class RegionBox:
    x: int
    y: int
    width: int
    height: int


class VisualRegionDetector:
    """Stub detector. Not used by default.

    To enable, implement detection of classes:
        verification_image / verification_input / continue_button
    and return a RegionBox, then crop and feed to PP-OCR.
    """

    async def detect(self, page: Page, target_class: str) -> RegionBox:
        raise NotImplementedError(
            "visual region detection is not enabled; use DOM locators instead "
            "(see architecture doc section 40)"
        )


def crop_region(image_bytes: bytes, region: RegionBox) -> bytes:
    from .image_utils import encode_png

    image = decode_image(image_bytes)
    h, w = image.shape[:2]
    x1 = max(0, min(region.x, w - 1))
    y1 = max(0, min(region.y, h - 1))
    x2 = max(x1 + 1, min(region.x + region.width, w))
    y2 = max(y1 + 1, min(region.y + region.height, h))
    return encode_png(image[y1:y2, x1:x2])
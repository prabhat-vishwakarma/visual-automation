"""Image preprocessing pipeline.

Supports multiple variants; nothing here assumes one transformation works for
every image. Variants are produced as in-memory PNG bytes.
"""

from __future__ import annotations

from .image_utils import decode_image, encode_png, grayscale_contrast, upscale

VALID_VARIANTS = {"raw", "upscale", "grayscale_contrast"}


class ImagePreprocessor:
    def __init__(self, variants: list[str]) -> None:
        unknown = set(variants) - VALID_VARIANTS
        if unknown:
            raise ValueError(f"unknown preprocessing variants: {sorted(unknown)}")
        self.variants = list(dict.fromkeys(variants))

    def generate_variants(self, image_bytes: bytes) -> list[tuple[str, bytes]]:
        """Return [(variant_name, png_bytes), ...] for configured variants."""
        image = decode_image(image_bytes)
        produced: list[tuple[str, bytes]] = []

        for name in self.variants:
            if name == "raw":
                produced.append((name, image_bytes))
            elif name == "upscale":
                produced.append((name, encode_png(upscale(image))))
            elif name == "grayscale_contrast":
                produced.append((name, encode_png(grayscale_contrast(image))))

        return produced
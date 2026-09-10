"""Unit tests for the image preprocessing pipeline."""

import cv2
import numpy as np
import pytest

from app.vision.preprocess import ImagePreprocessor

CHALLENGE_PNG = (
    __import__("pathlib").Path(__file__).resolve().parents[1]
    / "fixtures"
    / "test_site"
    / "challenge.png"
)


def _png_bytes() -> bytes:
    return CHALLENGE_PNG.read_bytes()


def test_raw_variant_returns_original_bytes():
    pre = ImagePreprocessor(["raw"])
    produced = pre.generate_variants(_png_bytes())
    assert produced == [("raw", _png_bytes())]


def test_all_variants_are_valid_pngs():
    pre = ImagePreprocessor(["raw", "upscale", "grayscale_contrast"])
    for name, data in pre.generate_variants(_png_bytes()):
        arr = np.frombuffer(data, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        assert image is not None, f"variant {name} did not decode"
        assert image.shape[0] > 0 and image.shape[1] > 0


def test_upscale_doubles_dimensions():
    pre = ImagePreprocessor(["upscale"])
    (_, data) = pre.generate_variants(_png_bytes())[0]
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    original = cv2.imdecode(
        np.frombuffer(_png_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR
    )
    assert image.shape[0] >= original.shape[0] * 2 - 1
    assert image.shape[1] >= original.shape[1] * 2 - 1


def test_unknown_variant_rejected():
    with pytest.raises(ValueError, match="unknown"):
        ImagePreprocessor(["raw", "bogus"])


def test_duplicate_variants_deduplicated():
    pre = ImagePreprocessor(["raw", "raw", "upscale"])
    produced = pre.generate_variants(_png_bytes())
    assert [name for name, _ in produced] == ["raw", "upscale"]


def test_invalid_image_raises():
    pre = ImagePreprocessor(["raw"])
    with pytest.raises(ValueError, match="decode"):
        pre.generate_variants(b"not an image")
"""Decode/denode helpers shared across the vision layer."""

from __future__ import annotations

import cv2
import numpy as np


def decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode PNG/JPEG bytes into an OpenCV BGR image."""
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("failed to decode image bytes")
    return image


def encode_png(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", image)
    if not ok:
        raise ValueError("failed to encode PNG")
    return encoded.tobytes()


def upscale(image: np.ndarray, factor: int = 2) -> np.ndarray:
    return cv2.resize(
        image,
        None,
        fx=factor,
        fy=factor,
        interpolation=cv2.INTER_CUBIC,
    )


def grayscale_contrast(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contrasted = cv2.normalize(
        gray,
        None,
        alpha=0,
        beta=255,
        norm_type=cv2.NORM_MINMAX,
    )
    return cv2.cvtColor(contrasted, cv2.COLOR_GRAY2BGR)
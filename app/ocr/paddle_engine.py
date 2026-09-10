"""Long-lived PP-OCR recognition engine.

The model is loaded once at application start and kept resident in process.
Inference input is an in-memory image; never re-load the model per capture.
"""

from __future__ import annotations

import time

import cv2
import numpy as np

from ..config import OcrConfig
from ..exceptions import OCRRecognitionError
from ..telemetry.logger import get_logger
from .models import OCRResult

logger = get_logger(__name__)


class OCREngine:
    def __init__(self, config: OcrConfig) -> None:
        self._config = config
        self._engine = None
        self._load_model()

    def _load_model(self) -> None:
        start = time.perf_counter()
        try:
            from paddleocr import PaddleOCR

            self._engine = PaddleOCR(
                lang=self._config.lang,
                ocr_version=self._map_ocr_version(self._config.model),
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        except Exception as exc:
            raise OCRRecognitionError(f"failed to load OCR model: {exc}") from exc
        elapsed = (time.perf_counter() - start) * 1000.0
        logger.info("ocr_model_loaded", latency_ms=round(elapsed, 1), lang=self._config.lang)

    @staticmethod
    def _map_ocr_version(model: str) -> str:
        """Map a configured model name to a PaddleOCR pipeline version.

        Recognized keys fall back to the closest available pipeline version.
        """
        lowered = model.lower()
        for version in ("v6", "v5", "v4", "v3"):
            if version in lowered:
                return f"PP-OCR{version}"
        return "PP-OCRv5"

    def recognize(self, image: bytes, variant: str = "raw") -> OCRResult:
        """Run recognition on encoded image bytes, return result + confidence."""
        start = time.perf_counter()
        array = self._decode(image)
        try:
            raw = self._engine.predict(array)
        except Exception as exc:
            raise OCRRecognitionError(f"OCR inference failed: {exc}") from exc

        text = "".join(self._extract_texts(raw))
        confidence = self._extract_confidence(raw)
        elapsed = (time.perf_counter() - start) * 1000.0

        logger.info(
            "ocr_inference_done",
            preprocessing_variant=variant,
            text=text,
            confidence=round(confidence, 3),
            latency_ms=round(elapsed, 1),
        )
        return OCRResult(
            text=text,
            confidence=confidence,
            preprocessing_variant=variant,
            latency_ms=elapsed,
        )

    @staticmethod
    def _decode(image: bytes) -> np.ndarray:
        arr = np.frombuffer(image, dtype=np.uint8)
        decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if decoded is None:
            raise OCRRecognitionError("failed to decode image for OCR")
        return decoded

    @staticmethod
    def _extract_texts(raw_results) -> list[str]:
        """Handle both PaddleOCR 3.x (dicts) and 2.x (nested lists) outputs."""
        if not raw_results:
            return []

        first = raw_results[0]
        # PaddleOCR 3.x: list of dict with 'rec_texts' / 'rec_text'
        if isinstance(first, dict):
            texts = first.get("rec_texts") or first.get("rec_text") or []
            return [str(t) for t in texts if t]
        # PaddleOCR 2.x: list of [box, (text, score)]
        if isinstance(first, (list, tuple)):
            return [
                str(item[1][0])
                for item in first
                if isinstance(item, (list, tuple)) and item[1]
            ]
        return []

    @staticmethod
    def _extract_confidence(raw_results) -> float:
        if not raw_results:
            return 0.0

        first = raw_results[0]
        if isinstance(first, dict):
            scores = first.get("rec_scores") or first.get("rec_score") or []
            if not scores:
                return 0.0
            return float(sum(scores) / len(scores))

        if isinstance(first, (list, tuple)):
            scores = [
                float(item[1][1])
                for item in first
                if isinstance(item, (list, tuple)) and item[1] and len(item[1]) > 1
            ]
            if not scores:
                return 0.0
            return sum(scores) / len(scores)

        return 0.0
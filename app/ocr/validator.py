"""OCR output validation.

OCR output is never trusted directly. Pipeline: strip whitespace, normalize
case, character/length check via regex, confidence threshold.
"""

from __future__ import annotations

import re

from ..telemetry.logger import get_logger
from .models import OCRResult, ValidationResult

logger = get_logger(__name__)


class OCRValidator:
    def __init__(self, pattern: str, min_confidence: float) -> None:
        self.pattern = re.compile(pattern)
        self.min_confidence = min_confidence

    def validate(self, result: OCRResult) -> ValidationResult:
        normalized = result.text.strip().upper()

        if result.confidence < self.min_confidence:
            return ValidationResult(
                accepted=False,
                normalized_text=normalized,
                reason="low_confidence",
            )

        if not self.pattern.fullmatch(normalized):
            return ValidationResult(
                accepted=False,
                normalized_text=normalized,
                reason="format_mismatch",
            )

        return ValidationResult(accepted=True, normalized_text=normalized, reason=None)

    def log_rejection(self, result: OCRResult, validation: ValidationResult) -> None:
        logger.warning(
            "ocr_rejected",
            preprocessing_variant=result.preprocessing_variant,
            text=result.text,
            confidence=round(result.confidence, 3),
            reason=validation.reason,
        )
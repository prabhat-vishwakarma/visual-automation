"""Unit tests for the OCR validator."""

from app.ocr.models import OCRResult
from app.ocr.validator import OCRValidator

PATTERN = "^[A-Z0-9]{5}$"
VALIDATOR = OCRValidator(pattern=PATTERN, min_confidence=0.85)


def _result(text: str, confidence: float) -> OCRResult:
    return OCRResult(
        text=text,
        confidence=confidence,
        preprocessing_variant="raw",
        latency_ms=1.0,
    )


def test_accepts_valid_text_and_confidence():
    validation = VALIDATOR.validate(_result("K7Q2P", 0.95))
    assert validation.accepted is True
    assert validation.normalized_text == "K7Q2P"
    assert validation.reason is None


def test_normalizes_case_and_whitespace():
    validation = VALIDATOR.validate(_result("  k7q2p ", 0.95))
    assert validation.accepted is True
    assert validation.normalized_text == "K7Q2P"


def test_rejects_low_confidence():
    validation = VALIDATOR.validate(_result("K7Q2P", 0.50))
    assert validation.accepted is False
    assert validation.reason == "low_confidence"


def test_rejects_format_mismatch():
    validation = VALIDATOR.validate(_result("K7Q2PPPP", 0.95))
    assert validation.accepted is False
    assert validation.reason == "format_mismatch"


def test_rejects_bad_characters():
    validation = VALIDATOR.validate(_result("K7Q2!", 0.95))
    assert validation.accepted is False
    assert validation.reason == "format_mismatch"


def test_confidence_boundary_exactly_at_threshold_is_accepted():
    validator = OCRValidator(pattern=PATTERN, min_confidence=0.85)
    validation = validator.validate(_result("A1B2C", 0.85))
    assert validation.accepted is True
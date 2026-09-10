"""Fixture-based OCR recognition test.

Requires the PP-OCR model. The first run downloads the model from PaddleOCR's
model zoo; subsequent runs use the local cache.
"""

from pathlib import Path

import pytest

from app.config import OcrConfig
from app.ocr.paddle_engine import OCREngine
from app.ocr.validator import OCRValidator
from app.vision.preprocess import ImagePreprocessor

REPO_ROOT = Path(__file__).resolve().parents[0]  # tests/unit
CHALLENGE_PNG = REPO_ROOT.parent / "fixtures" / "test_site" / "challenge.png"
EXPECTED = "K7Q2P"

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def engine() -> OCREngine:
    return OCREngine(OcrConfig(model="PP-OCRv5_mobile_rec", lang="en"))


def test_oc_reads_fixture_variant_with_multi_variant_loop(engine: OCREngine):
    validator = OCRValidator(pattern="^[A-Z0-9]{5}$", min_confidence=0.70)
    preprocessor = ImagePreprocessor(["raw", "upscale", "grayscale_contrast"])

    best_text = None
    for variant, image_bytes in preprocessor.generate_variants(
        CHALLENGE_PNG.read_bytes()
    ):
        result = engine.recognize(image_bytes, variant=variant)
        validation = validator.validate(result)
        if validation.accepted:
            best_text = validation.normalized_text
            break

    assert best_text is not None, "no preprocessing variant produced an accepted reading"

    # PP-OCR may confuse similar characters; accept exact or 1-edit-distance.
    if best_text != EXPECTED and levenshtein(best_text, EXPECTED) > 1:
        pytest.fail(f"OCR read {best_text!r}, expected {EXPECTED!r} (or 1 edit away)")


def levenshtein(a: str, b: str) -> int:
    row = range(len(b) + 1)
    for i, ca in enumerate(a, start=1):
        new_row = [i]
        for j, cb in enumerate(b, start=1):
            new_row.append(min(new_row[j - 1] + 1, row[j] + 1, row[j - 1] + (ca != cb)))
        row = new_row
    return row[-1]
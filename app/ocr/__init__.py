"""OCR layer: long-lived PP-OCR engine and result validation."""

from app.ocr.paddle_engine import OCREngine
from app.ocr.validator import OCRValidator

__all__ = ["OCREngine", "OCRValidator"]
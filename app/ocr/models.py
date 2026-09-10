"""Typed data contracts for OCR and validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class OCRResult:
    text: str
    confidence: float
    preprocessing_variant: str
    latency_ms: float
    completed_at: datetime | None = None


@dataclass
class ValidationResult:
    accepted: bool
    normalized_text: str
    reason: str | None


@dataclass
class WorkflowResult:
    success: bool
    final_state: str
    attempts: int
    reason: str | None
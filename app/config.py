"""Configuration model for the visual automation system.

All site-specific behavior lives in YAML configuration, never hard-coded
throughout the source tree. This module parses and validates that config.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator


class BrowserConfig(BaseModel):
    browser: str = "chromium"
    headless: bool = False
    persistent_profile: str = "./runtime/browser-profile"
    navigation_timeout_ms: int = 30000
    launch_args: list[str] = Field(default_factory=list)


class TargetConfig(BaseModel):
    start_url: str


class AuthenticationConfig(BaseModel):
    mode: str = "manual"
    authenticated_selector: str | None = None
    wait_timeout_seconds: int = 300


class SelectorsConfig(BaseModel):
    challenge_image: str
    challenge_input: str
    continue_button: str
    success_element: str
    rejection_element: str | None = None


class OcrConfig(BaseModel):
    model: str = "PP-OCRv6_small_rec"
    min_confidence: float = 0.85
    expected_regex: str = "^[A-Z0-9]{5}$"
    max_attempts: int = 3
    lang: str = "en"

    @field_validator("min_confidence")
    @classmethod
    def _confidence_in_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        return v

    @field_validator("max_attempts")
    @classmethod
    def _attempts_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("max_attempts must be >= 1")
        return v


class PreprocessingConfig(BaseModel):
    variants: list[str] = Field(
        default_factory=lambda: ["raw", "upscale", "grayscale_contrast"]
    )


class WorkflowConfig(BaseModel):
    target_wait_timeout_seconds: int = 30
    page_retry_limit: int = 2
    navigation_retry_limit: int = 2
    submit_retry_limit: int = 1
    post_submit_timeout_seconds: int = 15
    capture_retry_limit: int = 2


class ArtifactsConfig(BaseModel):
    save_failures: bool = True
    save_success_images: bool = False
    root: str = "./artifacts"


class AppConfig(BaseModel):
    browser: BrowserConfig
    target: TargetConfig
    authentication: AuthenticationConfig = Field(
        default_factory=AuthenticationConfig
    )
    selectors: SelectorsConfig
    ocr: OcrConfig = Field(default_factory=OcrConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    artifacts: ArtifactsConfig = Field(default_factory=ArtifactsConfig)


def load_config(path: str | Path) -> AppConfig:
    """Load and validate a YAML configuration file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    return AppConfig.model_validate(raw)
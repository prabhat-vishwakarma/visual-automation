"""Unit tests for configuration parsing."""

from pathlib import Path

import pytest

from app.config import AppConfig, load_config

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_YAML = REPO_ROOT / "config" / "site.yaml"
LOCAL_TEST_YAML = REPO_ROOT / "config" / "local-test.yaml"


def test_loads_site_config():
    config = load_config(SITE_YAML)
    assert isinstance(config, AppConfig)
    assert config.target.start_url.startswith("https://")
    assert config.selectors.challenge_image == '[data-testid="verification-image"]'
    assert config.ocr.min_confidence == 0.85
    assert config.preprocessing.variants == ["raw", "upscale", "grayscale_contrast"]


def test_loads_local_test_config():
    config = load_config(LOCAL_TEST_YAML)
    assert config.target.start_url == "http://127.0.0.1:8800/"
    assert config.authentication.authenticated_selector is None
    assert config.browser.headless is True


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_config(REPO_ROOT / "config" / "does-not-exist.yaml")


def test_invalid_confidence_rejected():
    import yaml

    raw = yaml.safe_load(SITE_YAML.read_text(encoding="utf-8"))
    raw["ocr"]["min_confidence"] = 1.5
    with pytest.raises(ValueError):
        AppConfig.model_validate(raw)


def test_invalid_regex_defaults_remain_valid():
    raw = SITE_YAML.read_text(encoding="utf-8")
    import yaml

    data = yaml.safe_load(raw)
    config = AppConfig.model_validate(data)
    assert config.ocr.expected_regex == "^[A-Z0-9]{5}$"
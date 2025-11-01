"""Tests for configuration management."""

import pytest
from app.config import settings


def test_settings_loaded():
    """Test that settings are loaded correctly."""
    assert settings.api_title == "Menu OCR API"
    assert settings.api_version == "1.0.0"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_redis_settings():
    """Test Redis configuration."""
    assert settings.redis_host == "localhost"
    assert settings.redis_port == 6379
    assert settings.redis_ttl == 3600


def test_ocr_settings():
    """Test OCR configuration."""
    assert settings.ocr_confidence_threshold == 0.7
    assert settings.max_image_size_mb == 10
    assert len(settings.allowed_extensions) > 0
    assert ".jpg" in settings.allowed_extensions


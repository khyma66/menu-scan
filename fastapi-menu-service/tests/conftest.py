"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import Mock, patch, AsyncMock


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis for all tests."""
    with patch("app.services.redis_cache.redis") as mock_redis:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=None)
        mock_client.setex = AsyncMock()
        mock_client.exists = AsyncMock(return_value=0)
        mock_client.delete = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis.Redis = Mock(return_value=mock_client)
        yield mock_client


@pytest.fixture(autouse=True)
def mock_supabase():
    """Mock Supabase for all tests."""
    with patch("app.services.supabase_client.SupabaseClient") as mock_supabase:
        mock_instance = Mock()
        mock_instance.save_ocr_result = AsyncMock(return_value=True)
        mock_supabase.return_value = mock_instance
        yield mock_instance


"""Pytest configuration and fixtures."""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from src.models.news_item import NewsItem
from src.models.source_config import (
    SourceConfig, 
    PollingConfig, 
    EventConfig, 
    UpdateMechanism,
    FeederConfig,
    ServiceConfig,
    RedisConfig,
    TemporalConfig,
    WebhookConfig,
    MonitoringConfig,
)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_news_item() -> NewsItem:
    """Create a sample news item for testing."""
    return NewsItem(
        title="Test News Article",
        description="This is a test news article description",
        link="https://example.com/news/test-article",
        publication_date=datetime(2024, 1, 1, 12, 0, 0),
        source_name="Test Source",
        source_type="rss",
        author="Test Author",
        categories=["technology", "news"],
        full_content="This is the full content of the test article.",
        media_urls=["https://example.com/image.jpg"],
    )


@pytest.fixture
def sample_polling_config() -> PollingConfig:
    """Create a sample polling configuration."""
    return PollingConfig(
        interval_seconds=300,
        max_concurrent_requests=2,
        retry_attempts=3,
        retry_delay_seconds=30,
        timeout_seconds=30,
    )


@pytest.fixture
def sample_event_config() -> EventConfig:
    """Create a sample event configuration."""
    return EventConfig(
        webhook_port=9001,
        webhook_path="/webhook/test",
        websocket_reconnect=True,
        event_buffer_size=1000,
        max_event_age_seconds=3600,
    )


@pytest.fixture
def sample_rss_source_config(sample_polling_config) -> SourceConfig:
    """Create a sample RSS source configuration."""
    return SourceConfig(
        type="rss",
        name="Test RSS Source",
        url="https://example.com/feed.rss",
        update_mechanism=UpdateMechanism.POLLING,
        enabled=True,
        polling_config=sample_polling_config,
        specific_config={
            "extract_full_content": True,
            "user_agent": "NewsFeeder/1.0",
        }
    )


@pytest.fixture
def sample_telegram_source_config(sample_event_config) -> SourceConfig:
    """Create a sample Telegram source configuration."""
    return SourceConfig(
        type="telegram_event",
        name="Test Telegram Source",
        url="https://t.me/test_channel",
        update_mechanism=UpdateMechanism.EVENT_DRIVEN,
        enabled=True,
        event_config=sample_event_config,
        specific_config={
            "api_id": "12345",
            "api_hash": "test_hash",
            "channel_username": "test_channel",
        }
    )


@pytest.fixture
def sample_feeder_config(sample_rss_source_config, sample_telegram_source_config) -> FeederConfig:
    """Create a sample feeder configuration."""
    return FeederConfig(
        service=ServiceConfig(
            name="test-feeder",
            check_interval_minutes=5,
            max_concurrent_sources=5,
        ),
        sources=[sample_rss_source_config, sample_telegram_source_config],
        redis=RedisConfig(
            host="localhost",
            port=6379,
            db=1,  # Use different DB for testing
        ),
        temporal=TemporalConfig(
            host="localhost",
            port=7233,
            namespace="test",
            task_queue="test-news-processing",
        ),
        webhook=WebhookConfig(
            base_port=9100,  # Different port range for testing
            port_range=50,
        ),
        monitoring=MonitoringConfig(
            health_check_port=8190,
            prometheus_port=8191,
            log_level="DEBUG",
        ),
    )


@pytest.fixture
def sample_config_dict() -> Dict[str, Any]:
    """Create a sample configuration dictionary."""
    return {
        "service": {
            "name": "test-feeder",
            "check_interval_minutes": 5,
            "max_concurrent_sources": 5,
        },
        "sources": [
            {
                "type": "rss",
                "name": "Test RSS",
                "url": "https://example.com/feed.rss",
                "update_mechanism": "polling",
                "enabled": True,
                "polling_config": {
                    "interval_seconds": 300,
                    "max_concurrent_requests": 1,
                    "retry_attempts": 3,
                },
                "specific_config": {
                    "extract_full_content": True,
                }
            },
            {
                "type": "telegram_event",
                "name": "Test Telegram",
                "url": "https://t.me/test_channel",
                "update_mechanism": "event_driven",
                "enabled": True,
                "event_config": {
                    "webhook_port": 9001,
                    "webhook_path": "/webhook/telegram",
                },
                "specific_config": {
                    "api_id": "12345",
                    "api_hash": "test_hash",
                }
            }
        ],
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 1,
        },
        "temporal": {
            "host": "localhost",
            "port": 7233,
            "namespace": "test",
            "task_queue": "test-processing",
        },
        "webhook": {
            "base_port": 9100,
            "port_range": 50,
        },
        "monitoring": {
            "health_check_port": 8190,
            "log_level": "DEBUG",
        },
    }
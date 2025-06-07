"""Tests for the source configuration models."""

import pytest
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


class TestPollingConfig:
    """Test cases for PollingConfig model."""
    
    def test_polling_config_creation(self, sample_polling_config):
        """Test basic PollingConfig creation."""
        assert sample_polling_config.interval_seconds == 300
        assert sample_polling_config.max_concurrent_requests == 2
        assert sample_polling_config.retry_attempts == 3
        assert sample_polling_config.retry_delay_seconds == 30
        assert sample_polling_config.timeout_seconds == 30
    
    def test_polling_config_defaults(self):
        """Test PollingConfig with default values."""
        config = PollingConfig()
        assert config.interval_seconds == 600  # 10 minutes default
        assert config.max_concurrent_requests == 1
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 30
        assert config.timeout_seconds == 30
    
    def test_polling_config_validation_interval_too_small(self):
        """Test validation fails for interval less than 60 seconds."""
        with pytest.raises(ValueError, match="Polling interval must be at least 60 seconds"):
            PollingConfig(interval_seconds=30)
    
    def test_polling_config_validation_max_requests_zero(self):
        """Test validation fails for zero max concurrent requests."""
        with pytest.raises(ValueError, match="Max concurrent requests must be at least 1"):
            PollingConfig(max_concurrent_requests=0)
    
    def test_polling_config_validation_negative_retries(self):
        """Test validation fails for negative retry attempts."""
        with pytest.raises(ValueError, match="Retry attempts cannot be negative"):
            PollingConfig(retry_attempts=-1)


class TestEventConfig:
    """Test cases for EventConfig model."""
    
    def test_event_config_creation(self, sample_event_config):
        """Test basic EventConfig creation."""
        assert sample_event_config.webhook_port == 9001
        assert sample_event_config.webhook_path == "/webhook/test"
        assert sample_event_config.websocket_reconnect is True
        assert sample_event_config.event_buffer_size == 1000
        assert sample_event_config.max_event_age_seconds == 3600
    
    def test_event_config_defaults(self):
        """Test EventConfig with default values."""
        config = EventConfig()
        assert config.webhook_port is None
        assert config.webhook_path == "/webhook"
        assert config.websocket_reconnect is True
        assert config.event_buffer_size == 1000
        assert config.max_event_age_seconds == 3600
    
    def test_event_config_validation_invalid_port(self):
        """Test validation fails for invalid webhook port."""
        with pytest.raises(ValueError, match="Webhook port must be between 1024 and 65535"):
            EventConfig(webhook_port=80)  # Too low
        
        with pytest.raises(ValueError, match="Webhook port must be between 1024 and 65535"):
            EventConfig(webhook_port=70000)  # Too high
    
    def test_event_config_validation_buffer_size_zero(self):
        """Test validation fails for zero buffer size."""
        with pytest.raises(ValueError, match="Event buffer size must be at least 1"):
            EventConfig(event_buffer_size=0)
    
    def test_event_config_validation_max_age_zero(self):
        """Test validation fails for zero max event age."""
        with pytest.raises(ValueError, match="Max event age must be at least 1 second"):
            EventConfig(max_event_age_seconds=0)


class TestSourceConfig:
    """Test cases for SourceConfig model."""
    
    def test_rss_source_config_creation(self, sample_rss_source_config):
        """Test RSS source configuration creation."""
        assert sample_rss_source_config.type == "rss"
        assert sample_rss_source_config.name == "Test RSS Source"
        assert sample_rss_source_config.url == "https://example.com/feed.rss"
        assert sample_rss_source_config.update_mechanism == UpdateMechanism.POLLING
        assert sample_rss_source_config.enabled is True
        assert sample_rss_source_config.polling_config is not None
        assert sample_rss_source_config.specific_config["extract_full_content"] is True
    
    def test_telegram_source_config_creation(self, sample_telegram_source_config):
        """Test Telegram source configuration creation."""
        assert sample_telegram_source_config.type == "telegram_event"
        assert sample_telegram_source_config.name == "Test Telegram Source"
        assert sample_telegram_source_config.update_mechanism == UpdateMechanism.EVENT_DRIVEN
        assert sample_telegram_source_config.event_config is not None
        assert sample_telegram_source_config.specific_config["api_id"] == "12345"
    
    def test_source_config_auto_creates_polling_config(self):
        """Test that polling config is auto-created for polling sources."""
        config = SourceConfig(
            type="rss",
            name="Test RSS",
            url="https://example.com/feed.rss",
            update_mechanism=UpdateMechanism.POLLING
        )
        assert config.polling_config is not None
        assert config.polling_config.interval_seconds == 600  # Default
    
    def test_source_config_auto_creates_event_config(self):
        """Test that event config is auto-created for event-driven sources."""
        config = SourceConfig(
            type="telegram_event",
            name="Test Telegram",
            url="https://t.me/test",
            update_mechanism=UpdateMechanism.EVENT_DRIVEN
        )
        assert config.event_config is not None
        assert config.event_config.webhook_path == "/webhook"  # Default
    
    def test_source_config_hybrid_creates_both_configs(self):
        """Test that hybrid sources get both polling and event configs."""
        config = SourceConfig(
            type="hybrid_source",
            name="Test Hybrid",
            url="https://example.com",
            update_mechanism=UpdateMechanism.HYBRID
        )
        assert config.polling_config is not None
        assert config.event_config is not None
    
    def test_source_config_validation_missing_type(self):
        """Test validation fails for missing source type."""
        with pytest.raises(ValueError, match="Source type is required"):
            SourceConfig(
                type="",
                name="Test",
                url="https://example.com",
                update_mechanism=UpdateMechanism.POLLING
            )
    
    def test_source_config_validation_missing_name(self):
        """Test validation fails for missing source name."""
        with pytest.raises(ValueError, match="Source name is required"):
            SourceConfig(
                type="rss",
                name="",
                url="https://example.com",
                update_mechanism=UpdateMechanism.POLLING
            )
    
    def test_source_config_validation_missing_url(self):
        """Test validation fails for missing source URL."""
        with pytest.raises(ValueError, match="Source URL is required"):
            SourceConfig(
                type="rss",
                name="Test",
                url="",
                update_mechanism=UpdateMechanism.POLLING
            )
    
    def test_source_config_from_dict(self):
        """Test creating SourceConfig from dictionary."""
        data = {
            "type": "rss",
            "name": "Test RSS",
            "url": "https://example.com/feed.rss",
            "update_mechanism": "polling",
            "enabled": True,
            "polling_config": {
                "interval_seconds": 300,
                "max_concurrent_requests": 2,
                "retry_attempts": 3,
            },
            "specific_config": {
                "extract_full_content": True,
            }
        }
        
        config = SourceConfig.from_dict(data)
        assert config.type == "rss"
        assert config.name == "Test RSS"
        assert config.update_mechanism == UpdateMechanism.POLLING
        assert config.polling_config.interval_seconds == 300
        assert config.specific_config["extract_full_content"] is True
    
    def test_source_config_to_dict(self, sample_rss_source_config):
        """Test converting SourceConfig to dictionary."""
        data = sample_rss_source_config.to_dict()
        
        assert data["type"] == "rss"
        assert data["name"] == "Test RSS Source"
        assert data["update_mechanism"] == "polling"
        assert data["enabled"] is True
        assert "polling_config" in data
        assert data["polling_config"]["interval_seconds"] == 300
        assert "specific_config" in data


class TestFeederConfig:
    """Test cases for FeederConfig model."""
    
    def test_feeder_config_creation(self, sample_feeder_config):
        """Test basic FeederConfig creation."""
        assert sample_feeder_config.service.name == "test-feeder"
        assert len(sample_feeder_config.sources) == 2
        assert sample_feeder_config.redis.host == "localhost"
        assert sample_feeder_config.temporal.namespace == "test"
        assert sample_feeder_config.webhook.base_port == 9100
        assert sample_feeder_config.monitoring.log_level == "DEBUG"
    
    def test_feeder_config_validation_no_sources(self):
        """Test validation fails when no sources are configured."""
        with pytest.raises(ValueError, match="At least one source must be configured"):
            FeederConfig(sources=[])
    
    def test_feeder_config_validation_duplicate_source_names(self):
        """Test validation fails for duplicate source names."""
        source1 = SourceConfig(
            type="rss",
            name="Duplicate Name",
            url="https://example1.com",
            update_mechanism=UpdateMechanism.POLLING
        )
        source2 = SourceConfig(
            type="rss",
            name="Duplicate Name",  # Same name
            url="https://example2.com",
            update_mechanism=UpdateMechanism.POLLING
        )
        
        with pytest.raises(ValueError, match="Source names must be unique"):
            FeederConfig(sources=[source1, source2])
    
    def test_feeder_config_from_dict(self, sample_config_dict):
        """Test creating FeederConfig from dictionary."""
        config = FeederConfig.from_dict(sample_config_dict)
        
        assert config.service.name == "test-feeder"
        assert len(config.sources) == 2
        assert config.sources[0].type == "rss"
        assert config.sources[1].type == "telegram_event"
        assert config.redis.db == 1
        assert config.temporal.namespace == "test"
    
    def test_feeder_config_to_dict(self, sample_feeder_config):
        """Test converting FeederConfig to dictionary."""
        data = sample_feeder_config.to_dict()
        
        assert "service" in data
        assert "sources" in data
        assert "redis" in data
        assert "temporal" in data
        assert "webhook" in data
        assert "monitoring" in data
        
        assert data["service"]["name"] == "test-feeder"
        assert len(data["sources"]) == 2
        assert data["redis"]["host"] == "localhost"
    
    def test_feeder_config_get_source_by_name(self, sample_feeder_config):
        """Test getting source by name."""
        source = sample_feeder_config.get_source_by_name("Test RSS Source")
        assert source is not None
        assert source.type == "rss"
        
        # Test non-existent source
        source = sample_feeder_config.get_source_by_name("Non-existent")
        assert source is None
    
    def test_feeder_config_get_sources_by_type(self, sample_feeder_config):
        """Test getting sources by type."""
        rss_sources = sample_feeder_config.get_sources_by_type("rss")
        assert len(rss_sources) == 1
        assert rss_sources[0].name == "Test RSS Source"
        
        telegram_sources = sample_feeder_config.get_sources_by_type("telegram_event")
        assert len(telegram_sources) == 1
        assert telegram_sources[0].name == "Test Telegram Source"
        
        # Test non-existent type
        unknown_sources = sample_feeder_config.get_sources_by_type("unknown")
        assert len(unknown_sources) == 0
    
    def test_feeder_config_get_enabled_sources(self, sample_feeder_config):
        """Test getting enabled sources."""
        enabled_sources = sample_feeder_config.get_enabled_sources()
        assert len(enabled_sources) == 2  # Both sources are enabled by default
        
        # Disable one source
        sample_feeder_config.sources[0].enabled = False
        enabled_sources = sample_feeder_config.get_enabled_sources()
        assert len(enabled_sources) == 1
        assert enabled_sources[0].name == "Test Telegram Source"


class TestConfigValidation:
    """Test cases for configuration validation."""
    
    def test_redis_config_validation(self):
        """Test Redis configuration validation."""
        # Valid config
        config = RedisConfig(host="localhost", port=6379, db=0)
        assert config.host == "localhost"
        
        # Invalid port
        with pytest.raises(ValueError, match="Redis port must be between 1 and 65535"):
            RedisConfig(port=0)
        
        with pytest.raises(ValueError, match="Redis port must be between 1 and 65535"):
            RedisConfig(port=70000)
        
        # Invalid DB
        with pytest.raises(ValueError, match="Redis DB must be non-negative"):
            RedisConfig(db=-1)
    
    def test_temporal_config_validation(self):
        """Test Temporal configuration validation."""
        # Valid config
        config = TemporalConfig(host="localhost", port=7233, namespace="test")
        assert config.namespace == "test"
        
        # Invalid port
        with pytest.raises(ValueError, match="Temporal port must be between 1 and 65535"):
            TemporalConfig(port=0)
        
        # Empty namespace
        with pytest.raises(ValueError, match="Temporal namespace is required"):
            TemporalConfig(namespace="")
        
        # Empty task queue
        with pytest.raises(ValueError, match="Temporal task queue is required"):
            TemporalConfig(task_queue="")
    
    def test_webhook_config_validation(self):
        """Test Webhook configuration validation."""
        # Valid config
        config = WebhookConfig(base_port=9000, port_range=100)
        assert config.base_port == 9000
        
        # Invalid base port
        with pytest.raises(ValueError, match="Base port must be between 1024 and 65535"):
            WebhookConfig(base_port=80)
        
        # Invalid port range
        with pytest.raises(ValueError, match="Port range must be at least 1"):
            WebhookConfig(port_range=0)
    
    def test_monitoring_config_validation(self):
        """Test Monitoring configuration validation."""
        # Valid config
        config = MonitoringConfig(health_check_port=8090, log_level="INFO")
        assert config.log_level == "INFO"
        
        # Invalid health check port
        with pytest.raises(ValueError, match="Health check port must be between 1024 and 65535"):
            MonitoringConfig(health_check_port=80)
        
        # Invalid log level
        with pytest.raises(ValueError, match="Invalid log level"):
            MonitoringConfig(log_level="INVALID")
    
    def test_service_config_validation(self):
        """Test Service configuration validation."""
        # Valid config
        config = ServiceConfig(name="test", check_interval_minutes=5)
        assert config.name == "test"
        
        # Invalid check interval
        with pytest.raises(ValueError, match="Check interval must be at least 1 minute"):
            ServiceConfig(check_interval_minutes=0)
        
        # Invalid max concurrent sources
        with pytest.raises(ValueError, match="Max concurrent sources must be at least 1"):
            ServiceConfig(max_concurrent_sources=0)
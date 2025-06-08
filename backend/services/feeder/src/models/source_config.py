"""Source configuration data models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class UpdateMechanism(Enum):
    """Update mechanism for news sources."""
    POLLING = "polling"
    EVENT_DRIVEN = "event_driven"
    HYBRID = "hybrid"


@dataclass
class PollingConfig:
    """Configuration for polling-based sources."""
    interval_seconds: int = 600  # 10 minutes default
    max_concurrent_requests: int = 1
    retry_attempts: int = 3
    retry_delay_seconds: int = 30
    timeout_seconds: int = 30
    
    def __post_init__(self):
        """Validate polling configuration."""
        if self.interval_seconds < 60:
            raise ValueError("Polling interval must be at least 60 seconds")
        if self.max_concurrent_requests < 1:
            raise ValueError("Max concurrent requests must be at least 1")
        if self.retry_attempts < 0:
            raise ValueError("Retry attempts cannot be negative")


@dataclass
class EventConfig:
    """Configuration for event-driven sources."""
    webhook_port: Optional[int] = None
    webhook_path: str = "/webhook"
    websocket_reconnect: bool = True
    event_buffer_size: int = 1000
    max_event_age_seconds: int = 3600
    
    def __post_init__(self):
        """Validate event configuration."""
        if self.webhook_port is not None and (self.webhook_port < 1024 or self.webhook_port > 65535):
            raise ValueError("Webhook port must be between 1024 and 65535")
        if self.event_buffer_size < 1:
            raise ValueError("Event buffer size must be at least 1")
        if self.max_event_age_seconds < 1:
            raise ValueError("Max event age must be at least 1 second")


@dataclass
class SourceConfig:
    """Configuration for a news source."""
    type: str
    name: str
    url: str
    update_mechanism: UpdateMechanism
    enabled: bool = True
    polling_config: Optional[PollingConfig] = None
    event_config: Optional[EventConfig] = None
    specific_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate source configuration."""
        if not self.type:
            raise ValueError("Source type is required")
        if not self.name:
            raise ValueError("Source name is required")
        if not self.url:
            raise ValueError("Source URL is required")
        
        # Ensure appropriate config is present for update mechanism
        if self.update_mechanism in [UpdateMechanism.POLLING, UpdateMechanism.HYBRID]:
            if self.polling_config is None:
                self.polling_config = PollingConfig()
        
        if self.update_mechanism in [UpdateMechanism.EVENT_DRIVEN, UpdateMechanism.HYBRID]:
            if self.event_config is None:
                self.event_config = EventConfig()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceConfig":
        """Create SourceConfig from dictionary."""
        # Parse update mechanism
        update_mechanism = UpdateMechanism(data["update_mechanism"])
        
        # Parse polling config
        polling_config = None
        if "polling_config" in data and data["polling_config"]:
            polling_config = PollingConfig(**data["polling_config"])
        
        # Parse event config
        event_config = None
        if "event_config" in data and data["event_config"]:
            event_config = EventConfig(**data["event_config"])
        
        return cls(
            type=data["type"],
            name=data["name"],
            url=data["url"],
            update_mechanism=update_mechanism,
            enabled=data.get("enabled", True),
            polling_config=polling_config,
            event_config=event_config,
            specific_config=data.get("specific_config", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "type": self.type,
            "name": self.name,
            "url": self.url,
            "update_mechanism": self.update_mechanism.value,
            "enabled": self.enabled,
            "specific_config": self.specific_config,
        }
        
        if self.polling_config:
            result["polling_config"] = {
                "interval_seconds": self.polling_config.interval_seconds,
                "max_concurrent_requests": self.polling_config.max_concurrent_requests,
                "retry_attempts": self.polling_config.retry_attempts,
                "retry_delay_seconds": self.polling_config.retry_delay_seconds,
                "timeout_seconds": self.polling_config.timeout_seconds,
            }
        
        if self.event_config:
            result["event_config"] = {
                "webhook_port": self.event_config.webhook_port,
                "webhook_path": self.event_config.webhook_path,
                "websocket_reconnect": self.event_config.websocket_reconnect,
                "event_buffer_size": self.event_config.event_buffer_size,
                "max_event_age_seconds": self.event_config.max_event_age_seconds,
            }
        
        return result


@dataclass
class WebhookConfig:
    """Global webhook configuration."""
    base_port: int = 9000
    port_range: int = 100
    auto_assign: bool = True
    health_check_path: str = "/health"
    max_retries: int = 10
    
    def __post_init__(self):
        """Validate webhook configuration."""
        if self.base_port < 1024 or self.base_port > 65535:
            raise ValueError("Base port must be between 1024 and 65535")
        if self.port_range < 1:
            raise ValueError("Port range must be at least 1")


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    max_connections: int = 10
    
    def __post_init__(self):
        """Validate Redis configuration."""
        if self.port < 1 or self.port > 65535:
            raise ValueError("Redis port must be between 1 and 65535")
        if self.db < 0:
            raise ValueError("Redis DB must be non-negative")


@dataclass
class TemporalConfig:
    """Temporal configuration."""
    host: str = "localhost"
    port: int = 7233
    namespace: str = "default"
    task_queue: str = "news-processing"
    workflow_timeout_seconds: int = 3600
    activity_timeout_seconds: int = 300
    
    def __post_init__(self):
        """Validate Temporal configuration."""
        if self.port < 1 or self.port > 65535:
            raise ValueError("Temporal port must be between 1 and 65535")
        if not self.namespace:
            raise ValueError("Temporal namespace is required")
        if not self.task_queue:
            raise ValueError("Temporal task queue is required")


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    health_check_port: int = 8090
    metrics_enabled: bool = True
    prometheus_port: int = 8091
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validate monitoring configuration."""
        if self.health_check_port < 1024 or self.health_check_port > 65535:
            raise ValueError("Health check port must be between 1024 and 65535")
        if self.prometheus_port < 1024 or self.prometheus_port > 65535:
            raise ValueError("Prometheus port must be between 1024 and 65535")
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Invalid log level")


@dataclass
class ServiceConfig:
    """Service-level configuration."""
    name: str = "news-feeder"
    check_interval_minutes: int = 10
    max_concurrent_sources: int = 10
    shutdown_timeout_seconds: int = 30
    
    def __post_init__(self):
        """Validate service configuration."""
        if self.check_interval_minutes < 1:
            raise ValueError("Check interval must be at least 1 minute")
        if self.max_concurrent_sources < 1:
            raise ValueError("Max concurrent sources must be at least 1")


@dataclass
class FeederConfig:
    """Complete feeder configuration."""
    service: ServiceConfig = field(default_factory=ServiceConfig)
    sources: List[SourceConfig] = field(default_factory=list)
    redis: RedisConfig = field(default_factory=RedisConfig)
    temporal: TemporalConfig = field(default_factory=TemporalConfig)
    webhook: WebhookConfig = field(default_factory=WebhookConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    def __post_init__(self):
        """Validate complete configuration."""
        if not self.sources:
            raise ValueError("At least one source must be configured")
        
        # Validate unique source names
        source_names = [source.name for source in self.sources]
        if len(source_names) != len(set(source_names)):
            raise ValueError("Source names must be unique")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeederConfig":
        """Create FeederConfig from dictionary."""
        # Parse service config
        service_data = data.get("service", {})
        service = ServiceConfig(**service_data)
        
        # Parse sources
        sources = []
        for source_data in data.get("sources", []):
            sources.append(SourceConfig.from_dict(source_data))
        
        # Parse Redis config
        redis_data = data.get("redis", {})
        redis = RedisConfig(**redis_data)
        
        # Parse Temporal config
        temporal_data = data.get("temporal", {})
        temporal = TemporalConfig(**temporal_data)
        
        # Parse webhook config
        webhook_data = data.get("webhook", {})
        webhook = WebhookConfig(**webhook_data)
        
        # Parse monitoring config
        monitoring_data = data.get("monitoring", {})
        monitoring = MonitoringConfig(**monitoring_data)
        
        return cls(
            service=service,
            sources=sources,
            redis=redis,
            temporal=temporal,
            webhook=webhook,
            monitoring=monitoring,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "service": {
                "name": self.service.name,
                "check_interval_minutes": self.service.check_interval_minutes,
                "max_concurrent_sources": self.service.max_concurrent_sources,
                "shutdown_timeout_seconds": self.service.shutdown_timeout_seconds,
            },
            "sources": [source.to_dict() for source in self.sources],
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "db": self.redis.db,
                "password": self.redis.password,
                "ssl": self.redis.ssl,
                "socket_timeout": self.redis.socket_timeout,
                "socket_connect_timeout": self.redis.socket_connect_timeout,
                "max_connections": self.redis.max_connections,
            },
            "temporal": {
                "host": self.temporal.host,
                "port": self.temporal.port,
                "namespace": self.temporal.namespace,
                "task_queue": self.temporal.task_queue,
                "workflow_timeout_seconds": self.temporal.workflow_timeout_seconds,
                "activity_timeout_seconds": self.temporal.activity_timeout_seconds,
            },
            "webhook": {
                "base_port": self.webhook.base_port,
                "port_range": self.webhook.port_range,
                "auto_assign": self.webhook.auto_assign,
                "health_check_path": self.webhook.health_check_path,
                "max_retries": self.webhook.max_retries,
            },
            "monitoring": {
                "health_check_port": self.monitoring.health_check_port,
                "metrics_enabled": self.monitoring.metrics_enabled,
                "prometheus_port": self.monitoring.prometheus_port,
                "log_level": self.monitoring.log_level,
            },
        }
    
    def get_source_by_name(self, name: str) -> Optional[SourceConfig]:
        """Get source configuration by name."""
        for source in self.sources:
            if source.name == name:
                return source
        return None
    
    def get_sources_by_type(self, source_type: str) -> List[SourceConfig]:
        """Get all sources of a specific type."""
        return [source for source in self.sources if source.type == source_type]
    
    def get_enabled_sources(self) -> List[SourceConfig]:
        """Get all enabled sources."""
        return [source for source in self.sources if source.enabled]
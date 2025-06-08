"""Configuration loading and validation."""

import os
import logging
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union

from ..models.source_config import FeederConfig


logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> FeederConfig:
    """Load configuration from file or environment variables."""
    if config_path:
        return load_config_from_file(config_path)
    
    # Try to find config file in standard locations
    config_locations = [
        os.getenv("CONFIG_FILE"),
        "config/config.yaml",
        "config/config.yml", 
        "config.yaml",
        "config.yml",
        "/app/config/config.yaml",
        "/etc/news-feeder/config.yaml",
    ]
    
    for location in config_locations:
        if location and Path(location).exists():
            logger.info(f"Loading configuration from {location}")
            return load_config_from_file(location)
    
    # If no config file found, create default config with environment overrides
    logger.info("No configuration file found, using default configuration with environment overrides")
    return get_default_config_with_env_overrides()


def load_config_from_file(config_path: str) -> FeederConfig:
    """Load configuration from a YAML or JSON file."""
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif config_path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        # Apply environment variable overrides
        data = apply_env_overrides(data)
        
        return load_config_from_dict(data)
        
    except Exception as e:
        logger.error(f"Failed to load configuration from {config_path}: {e}")
        raise


def load_config_from_dict(data: Dict[str, Any]) -> FeederConfig:
    """Load configuration from a dictionary."""
    try:
        # Validate the configuration data
        validate_config_dict(data)
        
        # Create FeederConfig from dictionary
        config = FeederConfig.from_dict(data)
        
        # Additional validation
        validate_config(config)
        
        logger.info(f"Loaded configuration with {len(config.sources)} sources")
        return config
        
    except Exception as e:
        logger.error(f"Failed to create configuration from dictionary: {e}")
        raise


def validate_config(config: FeederConfig) -> None:
    """Validate a FeederConfig instance."""
    # Basic validation is done in the dataclass __post_init__ methods
    # Additional validation can be added here
    
    # Validate source names are unique
    source_names = [source.name for source in config.sources]
    if len(source_names) != len(set(source_names)):
        duplicates = [name for name in source_names if source_names.count(name) > 1]
        raise ValueError(f"Duplicate source names found: {duplicates}")
    
    # Validate port conflicts
    used_ports = set()
    
    # Add monitoring ports
    if config.monitoring.health_check_port in used_ports:
        raise ValueError(f"Port conflict: {config.monitoring.health_check_port}")
    used_ports.add(config.monitoring.health_check_port)
    
    if config.monitoring.prometheus_port in used_ports:
        raise ValueError(f"Port conflict: {config.monitoring.prometheus_port}")
    used_ports.add(config.monitoring.prometheus_port)
    
    # Check webhook ports
    for source in config.sources:
        if source.event_config and source.event_config.webhook_port:
            if source.event_config.webhook_port in used_ports:
                raise ValueError(f"Port conflict: {source.event_config.webhook_port}")
            used_ports.add(source.event_config.webhook_port)
    
    logger.debug("Configuration validation passed")


def validate_config_dict(data: Dict[str, Any]) -> None:
    """Validate configuration dictionary structure."""
    required_fields = ["sources"]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Required configuration field missing: {field}")
    
    if not isinstance(data["sources"], list):
        raise ValueError("'sources' must be a list")
    
    if not data["sources"]:
        raise ValueError("At least one source must be configured")
    
    # Validate each source
    for i, source in enumerate(data["sources"]):
        if not isinstance(source, dict):
            raise ValueError(f"Source {i} must be a dictionary")
        
        required_source_fields = ["type", "name", "url", "update_mechanism"]
        for field in required_source_fields:
            if field not in source:
                raise ValueError(f"Source {i} missing required field: {field}")


def apply_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration data."""
    # Create a copy to avoid modifying the original
    config_data = data.copy()
    
    # Service configuration overrides
    if "service" not in config_data:
        config_data["service"] = {}
    
    service_env_map = {
        "FEEDER_SERVICE_NAME": "name",
        "FEEDER_CHECK_INTERVAL_MINUTES": ("check_interval_minutes", int),
        "FEEDER_MAX_CONCURRENT_SOURCES": ("max_concurrent_sources", int),
        "FEEDER_SHUTDOWN_TIMEOUT_SECONDS": ("shutdown_timeout_seconds", int),
    }
    
    for env_var, config_key in service_env_map.items():
        if isinstance(config_key, tuple):
            config_key, converter = config_key
        else:
            converter = str
        
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                config_data["service"][config_key] = converter(env_value)
            except ValueError as e:
                logger.warning(f"Invalid value for {env_var}: {env_value} ({e})")
    
    # Redis configuration overrides
    if "redis" not in config_data:
        config_data["redis"] = {}
    
    redis_env_map = {
        "REDIS_HOST": "host",
        "REDIS_PORT": ("port", int),
        "REDIS_DB": ("db", int),
        "REDIS_PASSWORD": "password",
        "REDIS_SSL": ("ssl", lambda x: x.lower() in ['true', '1', 'yes']),
        "REDIS_SOCKET_TIMEOUT": ("socket_timeout", int),
        "REDIS_SOCKET_CONNECT_TIMEOUT": ("socket_connect_timeout", int),
        "REDIS_MAX_CONNECTIONS": ("max_connections", int),
    }
    
    for env_var, config_key in redis_env_map.items():
        if isinstance(config_key, tuple):
            config_key, converter = config_key
        else:
            converter = str
        
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                config_data["redis"][config_key] = converter(env_value)
            except ValueError as e:
                logger.warning(f"Invalid value for {env_var}: {env_value} ({e})")
    
    # Temporal configuration overrides
    if "temporal" not in config_data:
        config_data["temporal"] = {}
    
    temporal_env_map = {
        "TEMPORAL_HOST": "host",
        "TEMPORAL_PORT": ("port", int),
        "TEMPORAL_NAMESPACE": "namespace",
        "TEMPORAL_TASK_QUEUE": "task_queue",
        "TEMPORAL_WORKFLOW_TIMEOUT_SECONDS": ("workflow_timeout_seconds", int),
        "TEMPORAL_ACTIVITY_TIMEOUT_SECONDS": ("activity_timeout_seconds", int),
    }
    
    for env_var, config_key in temporal_env_map.items():
        if isinstance(config_key, tuple):
            config_key, converter = config_key
        else:
            converter = str
        
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                config_data["temporal"][config_key] = converter(env_value)
            except ValueError as e:
                logger.warning(f"Invalid value for {env_var}: {env_value} ({e})")
    
    # Webhook configuration overrides
    if "webhook" not in config_data:
        config_data["webhook"] = {}
    
    webhook_env_map = {
        "WEBHOOK_BASE_PORT": ("base_port", int),
        "WEBHOOK_PORT_RANGE": ("port_range", int),
        "WEBHOOK_AUTO_ASSIGN": ("auto_assign", lambda x: x.lower() in ['true', '1', 'yes']),
        "WEBHOOK_HEALTH_CHECK_PATH": "health_check_path",
        "WEBHOOK_MAX_RETRIES": ("max_retries", int),
    }
    
    for env_var, config_key in webhook_env_map.items():
        if isinstance(config_key, tuple):
            config_key, converter = config_key
        else:
            converter = str
        
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                config_data["webhook"][config_key] = converter(env_value)
            except ValueError as e:
                logger.warning(f"Invalid value for {env_var}: {env_value} ({e})")
    
    # Monitoring configuration overrides
    if "monitoring" not in config_data:
        config_data["monitoring"] = {}
    
    monitoring_env_map = {
        "HEALTH_CHECK_PORT": ("health_check_port", int),
        "METRICS_ENABLED": ("metrics_enabled", lambda x: x.lower() in ['true', '1', 'yes']),
        "PROMETHEUS_PORT": ("prometheus_port", int),
        "LOG_LEVEL": "log_level",
    }
    
    for env_var, config_key in monitoring_env_map.items():
        if isinstance(config_key, tuple):
            config_key, converter = config_key
        else:
            converter = str
        
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                config_data["monitoring"][config_key] = converter(env_value)
            except ValueError as e:
                logger.warning(f"Invalid value for {env_var}: {env_value} ({e})")
    
    # Apply source-specific environment overrides
    config_data = apply_source_env_overrides(config_data)
    
    return config_data


def apply_source_env_overrides(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply source-specific environment variable overrides."""
    # Handle common source environment variables
    source_env_vars = {
        "TELEGRAM_API_ID": "telegram_api_id",
        "TELEGRAM_API_HASH": "telegram_api_hash", 
        "TELEGRAM_PHONE": "telegram_phone",
        "NEWS_API_TOKEN": "news_api_token",
        "WEBHOOK_AUTH_TOKEN": "webhook_auth_token",
        "WEBHOOK_SECRET": "webhook_secret",
    }
    
    # Apply to all sources that might use these variables
    for source in data.get("sources", []):
        specific_config = source.get("specific_config", {})
        
        for env_var, config_key in source_env_vars.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Map environment variables to source-specific config keys
                if env_var.startswith("TELEGRAM_") and source.get("type") == "telegram_event":
                    if env_var == "TELEGRAM_API_ID":
                        specific_config["api_id"] = env_value
                    elif env_var == "TELEGRAM_API_HASH":
                        specific_config["api_hash"] = env_value
                    elif env_var == "TELEGRAM_PHONE":
                        specific_config["phone"] = env_value
                
                elif env_var == "NEWS_API_TOKEN" and source.get("type") in ["websocket", "webhook"]:
                    specific_config["api_token"] = env_value
                
                elif env_var.startswith("WEBHOOK_") and source.get("type") == "webhook":
                    if env_var == "WEBHOOK_AUTH_TOKEN":
                        specific_config["auth_token"] = env_value
                    elif env_var == "WEBHOOK_SECRET":
                        specific_config["signature_secret"] = env_value
        
        source["specific_config"] = specific_config
    
    return data


def get_default_config() -> FeederConfig:
    """Get default configuration."""
    return FeederConfig()


def get_default_config_with_env_overrides() -> FeederConfig:
    """Get default configuration with environment variable overrides."""
    # Start with minimal default configuration
    default_data = {
        "service": {},
        "sources": [],
        "redis": {},
        "temporal": {},
        "webhook": {},
        "monitoring": {},
    }
    
    # Apply environment overrides
    config_data = apply_env_overrides(default_data)
    
    # If no sources are configured via environment, add a basic example
    if not config_data["sources"]:
        logger.warning("No sources configured. Service will start but won't process any news.")
    
    return load_config_from_dict(config_data)


def save_config_to_file(config: FeederConfig, file_path: str, format: str = "yaml") -> None:
    """Save configuration to a file."""
    config_dict = config.to_dict()
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if format.lower() in ['yaml', 'yml']:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        elif format.lower() == 'json':
            json.dump(config_dict, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    logger.info(f"Configuration saved to {file_path}")
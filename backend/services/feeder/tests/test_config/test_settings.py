"""Tests for configuration loading and validation."""

import pytest
import os
import tempfile
import yaml
import json
from pathlib import Path

from src.config.settings import (
    load_config_from_dict,
    load_config_from_file,
    validate_config,
    validate_config_dict,
    apply_env_overrides,
    get_default_config,
    save_config_to_file,
)
from src.models.source_config import FeederConfig, UpdateMechanism


class TestConfigLoading:
    """Test cases for configuration loading."""
    
    def test_load_config_from_dict(self, sample_config_dict):
        """Test loading configuration from dictionary."""
        config = load_config_from_dict(sample_config_dict)
        
        assert isinstance(config, FeederConfig)
        assert config.service.name == "test-feeder"
        assert len(config.sources) == 2
        assert config.sources[0].type == "rss"
        assert config.sources[1].type == "telegram_event"
    
    def test_load_config_from_yaml_file(self, sample_config_dict):
        """Test loading configuration from YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config_dict, f)
            yaml_file = f.name
        
        try:
            config = load_config_from_file(yaml_file)
            assert isinstance(config, FeederConfig)
            assert config.service.name == "test-feeder"
            assert len(config.sources) == 2
        finally:
            os.unlink(yaml_file)
    
    def test_load_config_from_json_file(self, sample_config_dict):
        """Test loading configuration from JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config_dict, f)
            json_file = f.name
        
        try:
            config = load_config_from_file(json_file)
            assert isinstance(config, FeederConfig)
            assert config.service.name == "test-feeder"
            assert len(config.sources) == 2
        finally:
            os.unlink(json_file)
    
    def test_load_config_from_nonexistent_file(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_config_from_file("/nonexistent/config.yaml")
    
    def test_load_config_from_unsupported_format(self):
        """Test loading configuration from unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            txt_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported configuration file format"):
                load_config_from_file(txt_file)
        finally:
            os.unlink(txt_file)
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        # Default config should fail validation because no sources are configured
        with pytest.raises(ValueError, match="At least one source must be configured"):
            get_default_config()


class TestConfigValidation:
    """Test cases for configuration validation."""
    
    def test_validate_config_dict_valid(self, sample_config_dict):
        """Test validation of valid configuration dictionary."""
        # Should not raise any exception
        validate_config_dict(sample_config_dict)
    
    def test_validate_config_dict_missing_sources(self):
        """Test validation fails for missing sources."""
        config_dict = {"service": {"name": "test"}}
        
        with pytest.raises(ValueError, match="Required configuration field missing: sources"):
            validate_config_dict(config_dict)
    
    def test_validate_config_dict_empty_sources(self):
        """Test validation fails for empty sources list."""
        config_dict = {"sources": []}
        
        with pytest.raises(ValueError, match="At least one source must be configured"):
            validate_config_dict(config_dict)
    
    def test_validate_config_dict_sources_not_list(self):
        """Test validation fails when sources is not a list."""
        config_dict = {"sources": "not a list"}
        
        with pytest.raises(ValueError, match="'sources' must be a list"):
            validate_config_dict(config_dict)
    
    def test_validate_config_dict_invalid_source(self):
        """Test validation fails for invalid source structure."""
        config_dict = {
            "sources": [
                "not a dict"  # Should be a dictionary
            ]
        }
        
        with pytest.raises(ValueError, match="Source 0 must be a dictionary"):
            validate_config_dict(config_dict)
    
    def test_validate_config_dict_source_missing_fields(self):
        """Test validation fails for source missing required fields."""
        config_dict = {
            "sources": [
                {
                    "type": "rss",
                    # Missing name, url, update_mechanism
                }
            ]
        }
        
        with pytest.raises(ValueError, match="Source 0 missing required field: name"):
            validate_config_dict(config_dict)
    
    def test_validate_config_instance(self, sample_feeder_config):
        """Test validation of FeederConfig instance."""
        # Should not raise any exception
        validate_config(sample_feeder_config)
    
    def test_validate_config_duplicate_source_names(self):
        """Test validation fails for duplicate source names."""
        from src.models.source_config import SourceConfig
        
        source1 = SourceConfig(
            type="rss",
            name="Duplicate",
            url="https://example1.com",
            update_mechanism=UpdateMechanism.POLLING
        )
        source2 = SourceConfig(
            type="rss",
            name="Duplicate",  # Same name
            url="https://example2.com",
            update_mechanism=UpdateMechanism.POLLING
        )
        
        # Validation happens during FeederConfig construction
        with pytest.raises(ValueError, match="Source names must be unique"):
            FeederConfig(sources=[source1, source2])


class TestEnvironmentOverrides:
    """Test cases for environment variable overrides."""
    
    def test_apply_env_overrides_service(self):
        """Test environment overrides for service configuration."""
        config_data = {"service": {}}
        
        # Set environment variables
        os.environ["FEEDER_SERVICE_NAME"] = "env-feeder"
        os.environ["FEEDER_CHECK_INTERVAL_MINUTES"] = "15"
        os.environ["FEEDER_MAX_CONCURRENT_SOURCES"] = "20"
        
        try:
            result = apply_env_overrides(config_data)
            
            assert result["service"]["name"] == "env-feeder"
            assert result["service"]["check_interval_minutes"] == 15
            assert result["service"]["max_concurrent_sources"] == 20
        finally:
            # Clean up environment variables
            for key in ["FEEDER_SERVICE_NAME", "FEEDER_CHECK_INTERVAL_MINUTES", "FEEDER_MAX_CONCURRENT_SOURCES"]:
                os.environ.pop(key, None)
    
    def test_apply_env_overrides_redis(self):
        """Test environment overrides for Redis configuration."""
        config_data = {"redis": {}}
        
        # Set environment variables
        os.environ["REDIS_HOST"] = "redis.example.com"
        os.environ["REDIS_PORT"] = "6380"
        os.environ["REDIS_DB"] = "2"
        os.environ["REDIS_SSL"] = "true"
        
        try:
            result = apply_env_overrides(config_data)
            
            assert result["redis"]["host"] == "redis.example.com"
            assert result["redis"]["port"] == 6380
            assert result["redis"]["db"] == 2
            assert result["redis"]["ssl"] is True
        finally:
            # Clean up environment variables
            for key in ["REDIS_HOST", "REDIS_PORT", "REDIS_DB", "REDIS_SSL"]:
                os.environ.pop(key, None)
    
    def test_apply_env_overrides_temporal(self):
        """Test environment overrides for Temporal configuration."""
        config_data = {"temporal": {}}
        
        # Set environment variables
        os.environ["TEMPORAL_HOST"] = "temporal.example.com"
        os.environ["TEMPORAL_PORT"] = "7234"
        os.environ["TEMPORAL_NAMESPACE"] = "production"
        os.environ["TEMPORAL_TASK_QUEUE"] = "prod-news-processing"
        
        try:
            result = apply_env_overrides(config_data)
            
            assert result["temporal"]["host"] == "temporal.example.com"
            assert result["temporal"]["port"] == 7234
            assert result["temporal"]["namespace"] == "production"
            assert result["temporal"]["task_queue"] == "prod-news-processing"
        finally:
            # Clean up environment variables
            for key in ["TEMPORAL_HOST", "TEMPORAL_PORT", "TEMPORAL_NAMESPACE", "TEMPORAL_TASK_QUEUE"]:
                os.environ.pop(key, None)
    
    def test_apply_env_overrides_webhook(self):
        """Test environment overrides for webhook configuration."""
        config_data = {"webhook": {}}
        
        # Set environment variables
        os.environ["WEBHOOK_BASE_PORT"] = "9500"
        os.environ["WEBHOOK_PORT_RANGE"] = "200"
        os.environ["WEBHOOK_AUTO_ASSIGN"] = "false"
        
        try:
            result = apply_env_overrides(config_data)
            
            assert result["webhook"]["base_port"] == 9500
            assert result["webhook"]["port_range"] == 200
            assert result["webhook"]["auto_assign"] is False
        finally:
            # Clean up environment variables
            for key in ["WEBHOOK_BASE_PORT", "WEBHOOK_PORT_RANGE", "WEBHOOK_AUTO_ASSIGN"]:
                os.environ.pop(key, None)
    
    def test_apply_env_overrides_monitoring(self):
        """Test environment overrides for monitoring configuration."""
        config_data = {"monitoring": {}}
        
        # Set environment variables
        os.environ["HEALTH_CHECK_PORT"] = "8095"
        os.environ["METRICS_ENABLED"] = "false"
        os.environ["PROMETHEUS_PORT"] = "8096"
        os.environ["LOG_LEVEL"] = "WARNING"
        
        try:
            result = apply_env_overrides(config_data)
            
            assert result["monitoring"]["health_check_port"] == 8095
            assert result["monitoring"]["metrics_enabled"] is False
            assert result["monitoring"]["prometheus_port"] == 8096
            assert result["monitoring"]["log_level"] == "WARNING"
        finally:
            # Clean up environment variables
            for key in ["HEALTH_CHECK_PORT", "METRICS_ENABLED", "PROMETHEUS_PORT", "LOG_LEVEL"]:
                os.environ.pop(key, None)
    
    def test_apply_env_overrides_invalid_values(self):
        """Test environment overrides with invalid values."""
        config_data = {"service": {}}
        
        # Set invalid environment variable
        os.environ["FEEDER_CHECK_INTERVAL_MINUTES"] = "not_a_number"
        
        try:
            # Should not raise exception, but should log warning
            result = apply_env_overrides(config_data)
            
            # Invalid value should be ignored
            assert "check_interval_minutes" not in result["service"]
        finally:
            os.environ.pop("FEEDER_CHECK_INTERVAL_MINUTES", None)
    
    def test_apply_source_env_overrides_telegram(self):
        """Test source-specific environment overrides for Telegram."""
        config_data = {
            "sources": [
                {
                    "type": "telegram_event",
                    "name": "Test Telegram",
                    "url": "https://t.me/test",
                    "update_mechanism": "event_driven",
                    "specific_config": {}
                }
            ]
        }
        
        # Set Telegram environment variables
        os.environ["TELEGRAM_API_ID"] = "123456"
        os.environ["TELEGRAM_API_HASH"] = "test_hash_value"
        os.environ["TELEGRAM_PHONE"] = "+1234567890"
        
        try:
            result = apply_env_overrides(config_data)
            
            specific_config = result["sources"][0]["specific_config"]
            assert specific_config["api_id"] == "123456"
            assert specific_config["api_hash"] == "test_hash_value"
            assert specific_config["phone"] == "+1234567890"
        finally:
            # Clean up environment variables
            for key in ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE"]:
                os.environ.pop(key, None)


class TestConfigSaving:
    """Test cases for configuration saving."""
    
    def test_save_config_to_yaml_file(self, sample_feeder_config):
        """Test saving configuration to YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_file = f.name
        
        try:
            save_config_to_file(sample_feeder_config, yaml_file, format="yaml")
            
            # Verify file was created and contains valid YAML
            assert Path(yaml_file).exists()
            
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            
            assert data["service"]["name"] == "test-feeder"
            assert len(data["sources"]) == 2
        finally:
            os.unlink(yaml_file)
    
    def test_save_config_to_json_file(self, sample_feeder_config):
        """Test saving configuration to JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_file = f.name
        
        try:
            save_config_to_file(sample_feeder_config, json_file, format="json")
            
            # Verify file was created and contains valid JSON
            assert Path(json_file).exists()
            
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            assert data["service"]["name"] == "test-feeder"
            assert len(data["sources"]) == 2
        finally:
            os.unlink(json_file)
    
    def test_save_config_unsupported_format(self, sample_feeder_config):
        """Test saving configuration with unsupported format."""
        with pytest.raises(ValueError, match="Unsupported format: txt"):
            save_config_to_file(sample_feeder_config, "test.txt", format="txt")
    
    def test_save_config_creates_directories(self, sample_feeder_config):
        """Test that saving configuration creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "subdir" / "config.yaml"
            
            save_config_to_file(sample_feeder_config, str(config_file))
            
            # Verify directory was created and file exists
            assert config_file.exists()
            assert config_file.parent.exists()
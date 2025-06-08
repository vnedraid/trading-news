"""Configuration management for the News Feeder Service."""

from .settings import (
    load_config,
    load_config_from_file,
    load_config_from_dict,
    validate_config,
    get_default_config,
)

__all__ = [
    "load_config",
    "load_config_from_file", 
    "load_config_from_dict",
    "validate_config",
    "get_default_config",
]
"""Source factory for creating source instances."""

import logging
from typing import Dict, Type, Optional

from ..models.source_config import SourceConfig, UpdateMechanism
from .base import BaseSource


class SourceFactory:
    """Factory for creating source instances based on configuration."""
    
    def __init__(self):
        """Initialize the source factory."""
        self.logger = logging.getLogger("source_factory")
        self._source_types: Dict[str, Type[BaseSource]] = {}
    
    def register_source_type(self, source_type: str, source_class: Type[BaseSource]):
        """Register a source type with its implementation class."""
        self.logger.debug(f"Registering source type '{source_type}' with class {source_class.__name__}")
        self._source_types[source_type] = source_class
    
    def get_registered_types(self) -> Dict[str, Type[BaseSource]]:
        """Get all registered source types."""
        return self._source_types.copy()
    
    def is_type_registered(self, source_type: str) -> bool:
        """Check if a source type is registered."""
        return source_type in self._source_types
    
    def create_source(self, config: SourceConfig) -> BaseSource:
        """Create a source instance from configuration."""
        source_type = config.type
        
        if source_type not in self._source_types:
            available_types = list(self._source_types.keys())
            raise ValueError(
                f"Unknown source type '{source_type}'. "
                f"Available types: {available_types}"
            )
        
        source_class = self._source_types[source_type]
        
        try:
            # Validate configuration for the source type
            self._validate_source_config(config, source_class)
            
            # Create source instance
            source = source_class(config)
            
            self.logger.info(
                f"Created source '{config.name}' of type '{source_type}' "
                f"with update mechanism '{config.update_mechanism.value}'"
            )
            
            return source
            
        except Exception as e:
            self.logger.error(f"Failed to create source '{config.name}': {e}")
            raise
    
    def _validate_source_config(self, config: SourceConfig, source_class: Type[BaseSource]):
        """Validate source configuration for the given source class."""
        # Check if source class supports the update mechanism
        if hasattr(source_class, 'SUPPORTED_UPDATE_MECHANISMS'):
            supported_mechanisms = source_class.SUPPORTED_UPDATE_MECHANISMS
            if config.update_mechanism not in supported_mechanisms:
                raise ValueError(
                    f"Source type '{config.type}' does not support "
                    f"update mechanism '{config.update_mechanism.value}'. "
                    f"Supported mechanisms: {[m.value for m in supported_mechanisms]}"
                )
        
        # Check required configuration based on update mechanism
        if config.update_mechanism in [UpdateMechanism.POLLING, UpdateMechanism.HYBRID]:
            if not config.polling_config:
                raise ValueError(
                    f"Polling configuration is required for source '{config.name}' "
                    f"with update mechanism '{config.update_mechanism.value}'"
                )
        
        if config.update_mechanism in [UpdateMechanism.EVENT_DRIVEN, UpdateMechanism.HYBRID]:
            if not config.event_config:
                raise ValueError(
                    f"Event configuration is required for source '{config.name}' "
                    f"with update mechanism '{config.update_mechanism.value}'"
                )
        
        # Validate source-specific configuration
        if hasattr(source_class, 'validate_config'):
            source_class.validate_config(config)


# Global source factory instance
_source_factory: Optional[SourceFactory] = None


def get_source_factory() -> SourceFactory:
    """Get the global source factory instance."""
    global _source_factory
    if _source_factory is None:
        _source_factory = SourceFactory()
        _register_builtin_sources(_source_factory)
    return _source_factory


def _register_builtin_sources(factory: SourceFactory):
    """Register built-in source types."""
    # Import and register source implementations
    # This will be done when we implement the actual sources
    
    try:
        # RSS Source
        from .rss_source import RSSSource
        factory.register_source_type("rss", RSSSource)
    except ImportError:
        logging.getLogger("source_factory").debug("RSS source not available")
    
    try:
        # Web Scraper Source
        from .polling.web_scraper_source import WebScraperSource
        factory.register_source_type("web_scraper", WebScraperSource)
    except ImportError:
        logging.getLogger("source_factory").debug("Web scraper source not available")
    
    try:
        # Telegram Event Source
        from .events.telegram_source import TelegramEventSource
        factory.register_source_type("telegram_event", TelegramEventSource)
    except ImportError:
        logging.getLogger("source_factory").debug("Telegram event source not available")
    
    try:
        # WebSocket Source
        from .events.websocket_source import WebSocketSource
        factory.register_source_type("websocket", WebSocketSource)
    except ImportError:
        logging.getLogger("source_factory").debug("WebSocket source not available")
    
    try:
        # Webhook Source
        from .events.webhook_source import WebhookSource
        factory.register_source_type("webhook", WebhookSource)
    except ImportError:
        logging.getLogger("source_factory").debug("Webhook source not available")


def create_source(config: SourceConfig) -> BaseSource:
    """Convenience function to create a source using the global factory."""
    return get_source_factory().create_source(config)


def register_source_type(source_type: str, source_class: Type[BaseSource]):
    """Convenience function to register a source type with the global factory."""
    get_source_factory().register_source_type(source_type, source_class)


def get_available_source_types() -> Dict[str, Type[BaseSource]]:
    """Get all available source types."""
    return get_source_factory().get_registered_types()
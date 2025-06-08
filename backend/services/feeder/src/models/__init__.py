"""Data models for the News Feeder Service."""

from .news_item import NewsItem
from .source_config import (
    SourceConfig,
    PollingConfig,
    EventConfig,
    UpdateMechanism,
    FeederConfig,
)
from .events import (
    NewsEvent,
    SourceEvent,
    EventType,
)

__all__ = [
    "NewsItem",
    "SourceConfig",
    "PollingConfig", 
    "EventConfig",
    "UpdateMechanism",
    "FeederConfig",
    "NewsEvent",
    "SourceEvent",
    "EventType",
]
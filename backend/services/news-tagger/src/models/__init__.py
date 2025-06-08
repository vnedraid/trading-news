"""Data models for the news tagger service."""

from .news_item import NewsItem, TaggedNewsItem
from .tagger_config import TaggerConfig, LLMConfig

__all__ = ["NewsItem", "TaggedNewsItem", "TaggerConfig", "LLMConfig"]
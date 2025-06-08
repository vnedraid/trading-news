"""Data models for the news feeder service."""

from .news_item import NewsItem
from .worker_config import WorkerConfig, RSSWorkerConfig

__all__ = ["NewsItem", "WorkerConfig", "RSSWorkerConfig"]
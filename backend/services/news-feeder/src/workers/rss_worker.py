"""RSS worker implementation for fetching news from RSS feeds."""

import asyncio
import time
from datetime import datetime, timezone
from typing import List, Optional
import feedparser

from .base_worker import BaseWorker
from models.news_item import NewsItem
from models.worker_config import RSSWorkerConfig


class RSSWorker(BaseWorker):
    """Worker for fetching news from RSS feeds."""

    def __init__(self, config: RSSWorkerConfig):
        """Initialize the RSS worker.
        
        Args:
            config: RSS worker configuration
        """
        super().__init__(config)
        self.rss_config = config
        self._polling_interval_seconds = self._parse_interval(config.polling_interval)

    def _parse_interval(self, interval: str) -> int:
        """Parse polling interval string to seconds.
        
        Args:
            interval: Interval string (e.g., "5m", "1h", "30s")
            
        Returns:
            Interval in seconds
        """
        if interval.endswith('s'):
            return int(interval[:-1])
        elif interval.endswith('m'):
            return int(interval[:-1]) * 60
        elif interval.endswith('h'):
            return int(interval[:-1]) * 3600
        elif interval.endswith('d'):
            return int(interval[:-1]) * 86400
        else:
            raise ValueError(f"Invalid interval format: {interval}")

    async def _wait_for_next_cycle(self) -> None:
        """Wait for the next polling cycle."""
        try:
            await asyncio.wait_for(
                self._stop_event.wait(), 
                timeout=self._polling_interval_seconds
            )
        except asyncio.TimeoutError:
            pass

    async def _fetch_news(self) -> List[NewsItem]:
        """Fetch news from RSS feed.
        
        Returns:
            List of news items from the RSS feed
        """
        self._logger.info(f"Fetching RSS feed from {self.rss_config.url}")
        
        try:
            # Parse RSS feed
            # Note: feedparser.parse is synchronous, but we run it in executor for async
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, self.rss_config.url)
            
            self._logger.info(f"RSS feed parsed successfully. Found {len(feed.entries)} entries")
            
            news_items = []
            
            for i, entry in enumerate(feed.entries, 1):
                try:
                    news_item = self._parse_entry(entry)
                    if news_item:
                        news_items.append(news_item)
                        self._logger.debug(f"Parsed entry {i}: {news_item.title[:100]}...")
                    else:
                        self._logger.debug(f"Skipped entry {i}: missing required fields")
                except Exception as e:
                    self._logger.warning(f"Failed to parse RSS entry {i}: {e}")
                    continue
            
            self._logger.info(f"Successfully parsed {len(news_items)} valid news items from {len(feed.entries)} entries")
            return news_items
            
        except Exception as e:
            self._logger.error(f"Failed to fetch RSS feed from {self.rss_config.url}: {e}")
            raise

    def _parse_entry(self, entry) -> Optional[NewsItem]:
        """Parse a single RSS entry into a NewsItem.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            NewsItem or None if parsing fails
        """
        try:
            # Extract basic fields
            title = getattr(entry, 'title', '').strip()
            link = getattr(entry, 'link', '').strip()
            summary = getattr(entry, 'summary', '').strip()
            
            # Skip entries with missing required fields
            if not title or not link:
                self._logger.debug(f"Skipping entry with missing title or link")
                return None
            
            # Parse published date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = self._parse_time_struct(entry.published_parsed)
            
            # Create NewsItem
            news_item = NewsItem(
                title=title,
                url=link,
                source=self.name,
                content=summary if summary else None,
                summary=summary if summary else None,
                published_at=published_at
            )
            
            return news_item
            
        except Exception as e:
            self._logger.warning(f"Failed to parse RSS entry: {e}")
            return None

    def _parse_time_struct(self, time_struct) -> Optional[datetime]:
        """Parse time struct to datetime.
        
        Args:
            time_struct: Time struct from feedparser
            
        Returns:
            Datetime object or None
        """
        if not time_struct:
            return None
        
        try:
            # Convert time struct to datetime
            timestamp = time.mktime(time_struct)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            self._logger.warning(f"Failed to parse time struct: {e}")
            return None

    def __repr__(self) -> str:
        """String representation of the RSS worker."""
        return f"RSSWorker(name='{self.name}', url='{self.rss_config.url}', status='{self.status.value}')"
"""RSS source implementation for news feeds."""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin

try:
    import feedparser
    import aiohttp
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

from src.sources.base import PollingSource
from src.models.source_config import SourceConfig, UpdateMechanism
from src.models.news_item import NewsItem


logger = logging.getLogger(__name__)


class RSSSource(PollingSource):
    """RSS feed source implementation."""
    
    # Define supported update mechanisms
    SUPPORTED_UPDATE_MECHANISMS = [UpdateMechanism.POLLING, UpdateMechanism.HYBRID]
    
    def __init__(self, config: SourceConfig):
        """Initialize RSS source with configuration."""
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("RSS source requires 'feedparser' and 'aiohttp' packages")
            
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        
    @classmethod
    def validate_config(cls, config: SourceConfig) -> None:
        """Validate RSS source configuration."""
        if not config.url:
            raise ValueError("RSS source requires a URL")
            
        if not config.url.startswith(('http://', 'https://')):
            raise ValueError("RSS source URL must start with http:// or https://")
        
    async def fetch_items(self) -> List[NewsItem]:
        """Fetch news items from RSS feed."""
        if not self._session:
            await self._initialize_session()
            
        try:
            # Fetch RSS feed
            async with self._session.get(self.config.url) as response:
                if response.status != 200:
                    self.logger.error(f"Failed to fetch RSS feed {self.config.url}: HTTP {response.status}")
                    return []
                    
                content = await response.text()
                
            # Parse RSS feed
            feed = feedparser.parse(content)
            
            if feed.bozo and feed.bozo_exception:
                self.logger.warning(f"RSS feed {self.config.url} has parsing issues: {feed.bozo_exception}")
                
            news_items = []
            
            for entry in feed.entries:
                try:
                    news_item = self._parse_entry(entry, feed)
                    if news_item and news_item.is_valid():
                        news_items.append(news_item)
                    else:
                        self.logger.debug(f"Skipping invalid RSS entry: {getattr(entry, 'title', 'No title')}")
                        
                except Exception as e:
                    self.logger.error(f"Error parsing RSS entry: {e}")
                    
            self.logger.info(f"Fetched {len(news_items)} news items from RSS feed: {self.config.name}")
            return news_items
            
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout fetching RSS feed: {self.config.url}")
            return []
        except Exception as e:
            self.logger.error(f"Error fetching RSS feed {self.config.url}: {e}")
            return []
            
    async def _initialize_session(self) -> None:
        """Initialize HTTP session."""
        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            'User-Agent': 'News-Feeder/1.0 (RSS Reader)',
            'Accept': 'application/rss+xml, application/xml, text/xml'
        }
        
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers=headers
        )
        
        self.logger.info(f"Initialized RSS source session: {self.config.name}")
        
    async def start(self):
        """Start the RSS source."""
        await self._initialize_session()
        await super().start()
        
    async def stop(self):
        """Stop the RSS source."""
        await super().stop()
        
        if self._session:
            await self._session.close()
            self._session = None
            
        self.logger.info(f"Cleaned up RSS source: {self.config.name}")
            
    def _parse_entry(self, entry, feed) -> Optional[NewsItem]:
        """Parse a single RSS entry into a NewsItem."""
        try:
            # Extract title
            title = getattr(entry, 'title', '').strip()
            if not title:
                return None
                
            # Extract description
            description = ''
            if hasattr(entry, 'summary'):
                description = entry.summary
            elif hasattr(entry, 'description'):
                description = entry.description
                
            # Clean up description (remove HTML tags if present)
            if description:
                import re
                description = re.sub(r'<[^>]+>', '', description).strip()
                
            # Extract link
            link = getattr(entry, 'link', '').strip()
            if not link:
                return None
                
            # Make link absolute if it's relative
            if link.startswith('/'):
                base_url = getattr(feed.feed, 'link', self.config.url)
                link = urljoin(base_url, link)
                
            # Extract publication date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6])
                except (TypeError, ValueError):
                    pass
                    
            if not pub_date and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                try:
                    pub_date = datetime(*entry.updated_parsed[:6])
                except (TypeError, ValueError):
                    pass
                    
            # Use current time if no date found
            if not pub_date:
                pub_date = datetime.now()
                
            # Extract author
            author = ''
            if hasattr(entry, 'author'):
                author = entry.author
            elif hasattr(entry, 'author_detail') and hasattr(entry.author_detail, 'name'):
                author = entry.author_detail.name
                
            # Extract categories/tags
            categories = []
            if hasattr(entry, 'tags'):
                categories = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
                
            # Create NewsItem
            news_item = NewsItem(
                title=title,
                description=description,
                link=link,
                publication_date=pub_date,
                source_name=self.config.name,
                source_type="rss",
                author=author,
                categories=categories
            )
            
            return news_item
            
        except Exception as e:
            self.logger.error(f"Error parsing RSS entry: {e}")
            return None
            
    async def test_connection(self) -> bool:
        """Test connection to RSS feed."""
        try:
            if not self._session:
                await self._initialize_session()
                
            async with self._session.get(self.config.url) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"RSS connection test failed for {self.config.url}: {e}")
            return False
            
    def get_source_info(self) -> dict:
        """Get information about this RSS source."""
        return {
            "type": "rss",
            "name": self.config.name,
            "url": self.config.url,
            "enabled": self.config.enabled,
            "polling_interval": self.config.polling_config.interval_seconds if self.config.polling_config else None,
            "max_requests_per_hour": self.config.polling_config.max_requests_per_hour if self.config.polling_config else None,
            "dependencies_available": DEPENDENCIES_AVAILABLE
        }
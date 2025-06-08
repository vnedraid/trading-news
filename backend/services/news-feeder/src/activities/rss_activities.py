"""RSS-related activities for Temporal workflows."""

import asyncio
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
import feedparser

from temporalio import activity

from models.news_item import NewsItem
from models.worker_config import RSSWorkerConfig


@activity.defn
async def fetch_rss_news(config_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch news from RSS feed.
    
    Args:
        config_dict: RSS worker configuration as dictionary
        
    Returns:
        List of news items as dictionaries from the RSS feed
    """
    # Convert dict back to RSSWorkerConfig
    config = RSSWorkerConfig.from_dict(config_dict)
    activity.logger.info(f"Fetching RSS feed from {config.url}")
    
    try:
        # Parse RSS feed
        # Note: feedparser.parse is synchronous, but we run it in executor for async
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, config.url)
        
        activity.logger.info(f"RSS feed parsed successfully. Found {len(feed.entries)} entries")
        
        news_items = []
        
        for i, entry in enumerate(feed.entries, 1):
            try:
                news_item = _parse_entry(entry, config.name)
                if news_item:
                    news_items.append(news_item.to_dict())  # Convert to dict
                    activity.logger.debug(f"Parsed entry {i}: {news_item.title[:100]}...")
                else:
                    activity.logger.debug(f"Skipped entry {i}: missing required fields")
            except Exception as e:
                activity.logger.warning(f"Failed to parse RSS entry {i}: {e}")
                continue
        
        activity.logger.info(f"Successfully parsed {len(news_items)} valid news items from {len(feed.entries)} entries")
        return news_items
        
    except Exception as e:
        activity.logger.error(f"Failed to fetch RSS feed from {config.url}: {e}")
        raise


@activity.defn
async def process_news_items(news_items: List[Dict[str, Any]]) -> None:
    """Process news items (placeholder for future processing logic).
    
    Args:
        news_items: List of news items as dictionaries to process
    """
    activity.logger.info(f"Processing {len(news_items)} news items")
    
    # For now, just log the news items
    # In the future, this could send to other workflows, save to database, etc.
    for item in news_items:
        activity.logger.info(f"Processing: {item['title']}")
    
    activity.logger.info(f"Completed processing {len(news_items)} news items")


def _parse_entry(entry, source_name: str) -> NewsItem:
    """Parse a single RSS entry into a NewsItem.
    
    Args:
        entry: RSS entry from feedparser
        source_name: Name of the RSS source
        
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
            activity.logger.debug(f"Skipping entry with missing title or link")
            return None
        
        # Parse published date
        published_at = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            published_at = _parse_time_struct(entry.published_parsed)
        
        # Create NewsItem
        news_item = NewsItem(
            title=title,
            url=link,
            source=source_name,
            content=summary if summary else None,
            summary=summary if summary else None,
            published_at=published_at
        )
        
        return news_item
        
    except Exception as e:
        activity.logger.warning(f"Failed to parse RSS entry: {e}")
        return None


def _parse_time_struct(time_struct) -> datetime:
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
        activity.logger.warning(f"Failed to parse time struct: {e}")
        return None
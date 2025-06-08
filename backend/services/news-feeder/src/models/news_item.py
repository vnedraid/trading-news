"""News item data model."""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import re
from urllib.parse import urlparse


class NewsItem:
    """Represents a news item from an RSS feed or other source."""

    def __init__(
        self,
        title: str,
        url: str,
        source: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        published_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ):
        """Initialize a NewsItem.
        
        Args:
            title: The title of the news item
            url: The URL of the news item
            source: The source identifier (e.g., worker name)
            content: The full content of the news item
            summary: A summary of the news item
            published_at: When the news was originally published
            created_at: When this item was created in our system
            tags: List of tags associated with the news item
        """
        self.title = self._validate_title(title)
        self.url = self._validate_url(url)
        self.source = self._validate_source(source)
        self.content = content
        self.summary = summary
        self.published_at = published_at
        self.created_at = created_at or datetime.now(timezone.utc)
        self.tags = tags or []

    def _validate_title(self, title: str) -> str:
        """Validate the title field."""
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")
        return title.strip()

    def _validate_url(self, url: str) -> str:
        """Validate the URL field."""
        if not url or not url.strip():
            raise ValueError("URL cannot be empty")
        
        url = url.strip()
        parsed = urlparse(url)
        
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        return url

    def _validate_source(self, source: str) -> str:
        """Validate the source field."""
        if not source or not source.strip():
            raise ValueError("Source cannot be empty")
        return source.strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the NewsItem to a dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "content": self.content,
            "summary": self.summary,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsItem":
        """Create a NewsItem from a dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        published_at = None
        if data.get("published_at"):
            published_at = datetime.fromisoformat(data["published_at"])
        
        return cls(
            title=data["title"],
            url=data["url"],
            source=data["source"],
            content=data.get("content"),
            summary=data.get("summary"),
            published_at=published_at,
            created_at=created_at,
            tags=data.get("tags", [])
        )

    def __repr__(self) -> str:
        """String representation of the NewsItem."""
        return f"NewsItem(title='{self.title}', source='{self.source}', url='{self.url}')"

    def __eq__(self, other) -> bool:
        """Check equality based on URL and source."""
        if not isinstance(other, NewsItem):
            return False
        return self.url == other.url and self.source == other.source
"""News item data models."""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
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


class TaggedNewsItem(NewsItem):
    """Represents a news item with LLM-generated tags."""

    def __init__(
        self,
        title: str,
        url: str,
        source: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        published_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        confidence_scores: Optional[Dict[str, float]] = None,
        model_used: str = "",
        tagged_at: Optional[datetime] = None
    ):
        """Initialize a TaggedNewsItem.
        
        Args:
            title: The title of the news item
            url: The URL of the news item
            source: The source identifier
            content: The full content of the news item
            summary: A summary of the news item
            published_at: When the news was originally published
            created_at: When this item was created in our system
            tags: List of LLM-generated tags
            confidence_scores: Confidence scores for each tag
            model_used: The LLM model used for tagging
            tagged_at: When the tagging was performed
        """
        super().__init__(title, url, source, content, summary, published_at, created_at, tags)
        
        self.confidence_scores = confidence_scores or {}
        self.model_used = self._validate_model_used(model_used)
        self.tagged_at = tagged_at or datetime.now(timezone.utc)
        
        self._validate_confidence_scores()

    def _validate_model_used(self, model_used: str) -> str:
        """Validate the model_used field."""
        if not model_used or not model_used.strip():
            raise ValueError("Model used cannot be empty")
        return model_used.strip()

    def _validate_confidence_scores(self) -> None:
        """Validate confidence scores match tags and are in valid range."""
        if self.tags and self.confidence_scores:
            # Check that all tags have confidence scores
            if set(self.tags) != set(self.confidence_scores.keys()):
                raise ValueError("Confidence scores must match tags")
            
            # Check that all scores are in valid range [0, 1]
            for tag, score in self.confidence_scores.items():
                if not (0 <= score <= 1):
                    raise ValueError("Confidence scores must be between 0 and 1")

    @classmethod
    def from_news_item(
        cls,
        news_item: NewsItem,
        tags: List[str],
        confidence_scores: Optional[Dict[str, float]] = None,
        model_used: str = ""
    ) -> "TaggedNewsItem":
        """Create a TaggedNewsItem from a NewsItem.
        
        Args:
            news_item: Original NewsItem
            tags: LLM-generated tags
            confidence_scores: Confidence scores for each tag
            model_used: The LLM model used for tagging
            
        Returns:
            TaggedNewsItem with inherited properties and new tagging data
        """
        return cls(
            title=news_item.title,
            url=news_item.url,
            source=news_item.source,
            content=news_item.content,
            summary=news_item.summary,
            published_at=news_item.published_at,
            created_at=news_item.created_at,
            tags=tags,
            confidence_scores=confidence_scores,
            model_used=model_used
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the TaggedNewsItem to a dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            "confidence_scores": self.confidence_scores,
            "model_used": self.model_used,
            "tagged_at": self.tagged_at.isoformat()
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaggedNewsItem":
        """Create a TaggedNewsItem from a dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        
        published_at = None
        if data.get("published_at"):
            published_at = datetime.fromisoformat(data["published_at"])
        
        tagged_at = None
        if data.get("tagged_at"):
            tagged_at = datetime.fromisoformat(data["tagged_at"])
        
        return cls(
            title=data["title"],
            url=data["url"],
            source=data["source"],
            content=data.get("content"),
            summary=data.get("summary"),
            published_at=published_at,
            created_at=created_at,
            tags=data.get("tags", []),
            confidence_scores=data.get("confidence_scores", {}),
            model_used=data.get("model_used", ""),
            tagged_at=tagged_at
        )

    def __repr__(self) -> str:
        """String representation of the TaggedNewsItem."""
        return f"TaggedNewsItem(title='{self.title}', tags={self.tags}, model='{self.model_used}')"
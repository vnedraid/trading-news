"""News item data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import json


@dataclass
class NewsItem:
    """Unified news item model for all source types."""
    
    title: str
    description: str
    link: str
    publication_date: datetime
    source_name: str
    source_type: str
    author: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    full_content: Optional[str] = None
    media_urls: List[str] = field(default_factory=list)
    content_hash: str = ""
    extracted_at: datetime = field(default_factory=datetime.now)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate content hash after initialization."""
        if not self.content_hash:
            self.content_hash = self.generate_content_hash()
    
    def generate_content_hash(self) -> str:
        """Generate SHA-256 hash for duplicate detection."""
        # Use title, link, and publication date for hash
        hash_content = {
            "title": self.title.strip().lower(),
            "link": self.link.strip(),
            "publication_date": self.publication_date.isoformat(),
        }
        
        # Create deterministic JSON string
        hash_string = json.dumps(hash_content, sort_keys=True)
        
        # Generate SHA-256 hash
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "publication_date": self.publication_date.isoformat(),
            "source_name": self.source_name,
            "source_type": self.source_type,
            "author": self.author,
            "categories": self.categories,
            "full_content": self.full_content,
            "media_urls": self.media_urls,
            "content_hash": self.content_hash,
            "extracted_at": self.extracted_at.isoformat(),
            "raw_data": self.raw_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsItem":
        """Create NewsItem from dictionary."""
        # Parse datetime fields
        publication_date = datetime.fromisoformat(data["publication_date"])
        extracted_at = datetime.fromisoformat(data["extracted_at"])
        
        return cls(
            title=data["title"],
            description=data["description"],
            link=data["link"],
            publication_date=publication_date,
            source_name=data["source_name"],
            source_type=data["source_type"],
            author=data.get("author"),
            categories=data.get("categories", []),
            full_content=data.get("full_content"),
            media_urls=data.get("media_urls", []),
            content_hash=data.get("content_hash", ""),
            extracted_at=extracted_at,
            raw_data=data.get("raw_data", {}),
        )
    
    def is_valid(self) -> bool:
        """Check if the news item has required fields."""
        return bool(
            self.title and 
            self.link and 
            self.source_name and 
            self.source_type and
            self.publication_date
        )
    
    def __str__(self) -> str:
        """String representation of the news item."""
        return f"NewsItem(title='{self.title[:50]}...', source='{self.source_name}')"
    
    def __repr__(self) -> str:
        """Detailed representation of the news item."""
        return (
            f"NewsItem("
            f"title='{self.title}', "
            f"source_name='{self.source_name}', "
            f"source_type='{self.source_type}', "
            f"publication_date='{self.publication_date}', "
            f"content_hash='{self.content_hash}'"
            f")"
        )
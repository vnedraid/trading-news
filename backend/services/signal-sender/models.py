from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RSSFeedRecord:
    """Модель записи RSS feed для торговых новостей"""
    title: str
    description: str
    link: str
    published_date: datetime
    source: str
    category: Optional[str] = None
    sentiment: Optional[str] = None  # positive, negative, neutral
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "link": self.link,
            "published_date": self.published_date.isoformat(),
            "source": self.source,
            "category": self.category,
            "sentiment": self.sentiment
        }
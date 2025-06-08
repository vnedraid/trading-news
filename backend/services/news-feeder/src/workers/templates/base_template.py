"""Base template for RSS workers."""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging

from models.news_item import NewsItem


class RSSTemplate(ABC):
    """Abstract base class for RSS feed templates."""
    
    def __init__(self, template_name: str, source_name: str):
        """Initialize the RSS template.
        
        Args:
            template_name: Name of the template (e.g., 'kommersant', 'reuters')
            source_name: Name of the news source
        """
        self.template_name = template_name
        self.source_name = source_name
        self.logger = logging.getLogger(f"{__name__}.{template_name}")
    
    @abstractmethod
    def parse_entry(self, entry) -> Optional[NewsItem]:
        """Parse a single RSS entry into a NewsItem.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            NewsItem or None if parsing fails
        """
        pass
    
    @abstractmethod
    def validate_feed(self, feed) -> bool:
        """Validate if the feed matches this template's expected format.
        
        Args:
            feed: Parsed feed from feedparser
            
        Returns:
            True if feed is compatible with this template
        """
        pass
    
    def get_field_mapping(self) -> Dict[str, str]:
        """Get field mapping for this template.
        
        Returns:
            Dictionary mapping NewsItem fields to RSS entry fields
        """
        return {
            'title': 'title',
            'url': 'link', 
            'content': 'summary',
            'summary': 'summary',
            'published_at': 'published_parsed'
        }
    
    def extract_field(self, entry, field_name: str, default: Any = None) -> Any:
        """Extract a field from RSS entry with fallback options.
        
        Args:
            entry: RSS entry from feedparser
            field_name: Name of the field to extract
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        # Try direct field access
        if hasattr(entry, field_name):
            value = getattr(entry, field_name, default)
            if value and str(value).strip():
                return str(value).strip() if isinstance(value, str) else value
        
        # Try alternative field names
        alternatives = self.get_field_alternatives().get(field_name, [])
        for alt_field in alternatives:
            if hasattr(entry, alt_field):
                value = getattr(entry, alt_field, default)
                if value and str(value).strip():
                    return str(value).strip() if isinstance(value, str) else value
        
        return default
    
    def get_field_alternatives(self) -> Dict[str, List[str]]:
        """Get alternative field names for common RSS fields.
        
        Returns:
            Dictionary mapping field names to list of alternatives
        """
        return {
            'title': ['title'],
            'link': ['link', 'guid'],
            'summary': ['summary', 'description', 'content'],
            'content': ['content', 'summary', 'description'],
            'published_parsed': ['published_parsed', 'updated_parsed'],
            'author': ['author', 'dc_creator'],
            'category': ['category', 'tags']
        }
    
    def parse_datetime(self, time_struct) -> Optional[datetime]:
        """Parse time struct to datetime.
        
        Args:
            time_struct: Time struct from feedparser
            
        Returns:
            Datetime object or None
        """
        if not time_struct:
            return None
        
        try:
            timestamp = time.mktime(time_struct)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception as e:
            self.logger.warning(f"Failed to parse time struct: {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content.
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags (basic cleanup)
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def extract_categories(self, entry) -> List[str]:
        """Extract categories/tags from RSS entry.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            List of category strings
        """
        categories = []
        
        # Try tags field
        if hasattr(entry, 'tags') and entry.tags:
            for tag in entry.tags:
                if hasattr(tag, 'term'):
                    categories.append(tag.term)
                elif isinstance(tag, str):
                    categories.append(tag)
        
        # Try category field
        category = self.extract_field(entry, 'category')
        if category:
            categories.append(category)
        
        return [cat.strip() for cat in categories if cat and cat.strip()]
    
    def should_skip_entry(self, entry) -> bool:
        """Determine if an entry should be skipped.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            True if entry should be skipped
        """
        # Skip if missing required fields
        title = self.extract_field(entry, 'title')
        link = self.extract_field(entry, 'link')
        
        if not title or not link:
            self.logger.debug("Skipping entry with missing title or link")
            return True
        
        return False
    
    def get_template_info(self) -> Dict[str, Any]:
        """Get information about this template.
        
        Returns:
            Dictionary with template metadata
        """
        return {
            'name': self.template_name,
            'source': self.source_name,
            'field_mapping': self.get_field_mapping(),
            'field_alternatives': self.get_field_alternatives()
        }
"""Generic RSS template for standard RSS feeds."""

from typing import Optional
from .base_template import RSSTemplate
from models.news_item import NewsItem


class GenericRSSTemplate(RSSTemplate):
    """Generic template for standard RSS 2.0 feeds."""
    
    def __init__(self, source_name: str = "Generic RSS"):
        """Initialize the generic RSS template."""
        super().__init__("generic", source_name)
    
    def parse_entry(self, entry) -> Optional[NewsItem]:
        """Parse a single RSS entry into a NewsItem.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            NewsItem or None if parsing fails
        """
        try:
            if self.should_skip_entry(entry):
                return None
            
            # Extract basic fields
            title = self.extract_field(entry, 'title')
            link = self.extract_field(entry, 'link')
            summary = self.extract_field(entry, 'summary')
            content = self.extract_field(entry, 'content')
            
            # Use content if available, otherwise summary
            article_content = content if content else summary
            article_summary = summary if summary else content
            
            # Clean text content
            if article_content:
                article_content = self.clean_text(article_content)
            if article_summary:
                article_summary = self.clean_text(article_summary)
            
            # Parse published date
            published_at = None
            time_struct = self.extract_field(entry, 'published_parsed')
            if time_struct:
                published_at = self.parse_datetime(time_struct)
            
            # Extract author
            author = self.extract_field(entry, 'author')
            
            # Extract categories
            categories = self.extract_categories(entry)
            
            # Create NewsItem
            news_item = NewsItem(
                title=title,
                url=link,
                source=self.source_name,
                content=article_content,
                summary=article_summary,
                published_at=published_at,
                author=author if author else None,
                tags=categories if categories else None
            )
            
            return news_item
            
        except Exception as e:
            self.logger.warning(f"Failed to parse RSS entry: {e}")
            return None
    
    def validate_feed(self, feed) -> bool:
        """Validate if the feed matches this template's expected format.
        
        Args:
            feed: Parsed feed from feedparser
            
        Returns:
            True if feed is compatible with this template
        """
        # Generic template accepts any valid RSS feed
        if not hasattr(feed, 'entries') or not feed.entries:
            return False
        
        # Check if at least one entry has basic required fields
        for entry in feed.entries[:3]:  # Check first 3 entries
            if (hasattr(entry, 'title') and entry.title and 
                hasattr(entry, 'link') and entry.link):
                return True
        
        return False
    
    def get_field_alternatives(self):
        """Get alternative field names for generic RSS feeds."""
        return {
            'title': ['title'],
            'link': ['link', 'guid', 'id'],
            'summary': ['summary', 'description'],
            'content': ['content', 'summary', 'description'],
            'published_parsed': ['published_parsed', 'updated_parsed', 'created_parsed'],
            'author': ['author', 'dc_creator', 'creator'],
            'category': ['category', 'tags']
        }
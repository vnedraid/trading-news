"""BBC RSS template for BBC News feeds."""

import re
from typing import Optional
from .base_template import RSSTemplate
from models.news_item import NewsItem


class BBCRSSTemplate(RSSTemplate):
    """Template for BBC News RSS feeds."""
    
    def __init__(self, source_name: str = "BBC News"):
        """Initialize the BBC RSS template."""
        super().__init__("bbc", source_name)
    
    def parse_entry(self, entry) -> Optional[NewsItem]:
        """Parse a single BBC RSS entry into a NewsItem.
        
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
            
            # Clean BBC-specific formatting
            if title:
                title = self.clean_bbc_title(title)
            
            if summary:
                summary = self.clean_bbc_content(summary)
            
            # Parse published date
            published_at = None
            time_struct = self.extract_field(entry, 'published_parsed')
            if time_struct:
                published_at = self.parse_datetime(time_struct)
            
            # Extract BBC-specific fields
            categories = self.extract_bbc_categories(entry)
            
            # Create NewsItem
            news_item = NewsItem(
                title=title,
                url=link,
                source=self.source_name,
                content=summary,
                summary=summary,
                published_at=published_at,
                tags=categories if categories else None
            )
            
            return news_item
            
        except Exception as e:
            self.logger.warning(f"Failed to parse BBC RSS entry: {e}")
            return None
    
    def validate_feed(self, feed) -> bool:
        """Validate if the feed is from BBC.
        
        Args:
            feed: Parsed feed from feedparser
            
        Returns:
            True if feed is from BBC
        """
        if not hasattr(feed, 'feed') or not hasattr(feed, 'entries'):
            return False
        
        # Check feed title or link for BBC indicators
        feed_info = feed.feed
        
        bbc_indicators = [
            'bbc',
            'bbc.com',
            'bbc.co.uk',
            'british broadcasting'
        ]
        
        # Check feed title
        if hasattr(feed_info, 'title') and feed_info.title:
            title_lower = feed_info.title.lower()
            if any(indicator in title_lower for indicator in bbc_indicators):
                return True
        
        # Check feed link
        if hasattr(feed_info, 'link') and feed_info.link:
            link_lower = feed_info.link.lower()
            if any(indicator in link_lower for indicator in bbc_indicators):
                return True
        
        # Check entry links
        for entry in feed.entries[:3]:
            if hasattr(entry, 'link') and entry.link:
                link_lower = entry.link.lower()
                if any(indicator in link_lower for indicator in ['bbc.com', 'bbc.co.uk']):
                    return True
        
        return False
    
    def clean_bbc_title(self, title: str) -> str:
        """Clean BBC-specific title formatting.
        
        Args:
            title: Raw title text
            
        Returns:
            Cleaned title
        """
        if not title:
            return ""
        
        # Remove common BBC prefixes/suffixes
        title = title.strip()
        
        # Remove "BBC News -" prefix if present
        title = re.sub(r'^BBC\s*News\s*-\s*', '', title, flags=re.IGNORECASE)
        
        # Clean HTML entities and tags
        title = self.clean_text(title)
        
        return title
    
    def clean_bbc_content(self, content: str) -> str:
        """Clean BBC-specific content formatting.
        
        Args:
            content: Raw content text
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Clean HTML and normalize whitespace
        content = self.clean_text(content)
        
        # Remove common BBC footer text
        footer_patterns = [
            r'©.*BBC.*$',
            r'Read more.*$',
            r'Follow BBC.*$'
        ]
        
        for pattern in footer_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content.strip()
    
    def extract_bbc_categories(self, entry) -> list:
        """Extract categories from BBC entry.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            List of categories
        """
        categories = self.extract_categories(entry)
        
        # Add BBC-specific category detection from URL patterns
        link = self.extract_field(entry, 'link', '')
        if link:
            url_categories = {
                'UK': ['/uk/', '/england/', '/scotland/', '/wales/', '/northern-ireland/'],
                'World': ['/world/', '/international/'],
                'Business': ['/business/', '/economy/'],
                'Technology': ['/technology/', '/tech/'],
                'Science': ['/science/', '/health/'],
                'Entertainment': ['/entertainment/', '/culture/'],
                'Sports': ['/sport/', '/sports/'],
                'Politics': ['/politics/', '/government/']
            }
            
            link_lower = link.lower()
            for category, patterns in url_categories.items():
                if any(pattern in link_lower for pattern in patterns):
                    if category not in categories:
                        categories.append(category)
        
        # Detect categories from content patterns
        title = self.extract_field(entry, 'title', '')
        content = self.extract_field(entry, 'summary', '')
        text_to_check = f"{title} {content}".lower()
        
        content_categories = {
            'Breaking News': ['breaking', 'urgent', 'developing'],
            'Weather': ['weather', 'storm', 'rain', 'snow', 'temperature'],
            'Health': ['health', 'nhs', 'hospital', 'medical', 'doctor'],
            'Education': ['school', 'university', 'student', 'education'],
            'Crime': ['police', 'court', 'crime', 'arrest', 'investigation']
        }
        
        for category, keywords in content_categories.items():
            if any(keyword in text_to_check for keyword in keywords):
                if category not in categories:
                    categories.append(category)
        
        return categories
    
    def get_field_alternatives(self):
        """Get alternative field names for BBC RSS feeds."""
        return {
            'title': ['title'],
            'link': ['link', 'guid'],
            'summary': ['summary', 'description'],
            'content': ['summary', 'description'],
            'published_parsed': ['published_parsed', 'updated_parsed'],
            'author': ['author', 'dc_creator'],
            'category': ['category', 'tags']
        }
"""Reuters RSS template for Reuters feeds."""

import re
from typing import Optional
from .base_template import RSSTemplate
from models.news_item import NewsItem


class ReutersRSSTemplate(RSSTemplate):
    """Template for Reuters RSS feeds."""
    
    def __init__(self, source_name: str = "Reuters"):
        """Initialize the Reuters RSS template."""
        super().__init__("reuters", source_name)
    
    def parse_entry(self, entry) -> Optional[NewsItem]:
        """Parse a single Reuters RSS entry into a NewsItem.
        
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
            
            # Clean Reuters-specific formatting
            if title:
                title = self.clean_reuters_title(title)
            
            if summary:
                summary = self.clean_reuters_content(summary)
            
            # Parse published date
            published_at = None
            time_struct = self.extract_field(entry, 'published_parsed')
            if time_struct:
                published_at = self.parse_datetime(time_struct)
            
            # Extract Reuters-specific fields
            author = self.extract_reuters_author(entry)
            categories = self.extract_reuters_categories(entry)
            
            # Create NewsItem
            news_item = NewsItem(
                title=title,
                url=link,
                source=self.source_name,
                content=summary,
                summary=summary,
                published_at=published_at,
                author=author,
                tags=categories if categories else None
            )
            
            return news_item
            
        except Exception as e:
            self.logger.warning(f"Failed to parse Reuters RSS entry: {e}")
            return None
    
    def validate_feed(self, feed) -> bool:
        """Validate if the feed is from Reuters.
        
        Args:
            feed: Parsed feed from feedparser
            
        Returns:
            True if feed is from Reuters
        """
        if not hasattr(feed, 'feed') or not hasattr(feed, 'entries'):
            return False
        
        # Check feed title or link for Reuters indicators
        feed_info = feed.feed
        
        reuters_indicators = [
            'reuters',
            'reuters.com'
        ]
        
        # Check feed title
        if hasattr(feed_info, 'title') and feed_info.title:
            title_lower = feed_info.title.lower()
            if any(indicator in title_lower for indicator in reuters_indicators):
                return True
        
        # Check feed link
        if hasattr(feed_info, 'link') and feed_info.link:
            link_lower = feed_info.link.lower()
            if any(indicator in link_lower for indicator in reuters_indicators):
                return True
        
        # Check entry links
        for entry in feed.entries[:3]:
            if hasattr(entry, 'link') and entry.link:
                link_lower = entry.link.lower()
                if 'reuters.com' in link_lower:
                    return True
        
        return False
    
    def clean_reuters_title(self, title: str) -> str:
        """Clean Reuters-specific title formatting.
        
        Args:
            title: Raw title text
            
        Returns:
            Cleaned title
        """
        if not title:
            return ""
        
        # Remove common Reuters prefixes/suffixes
        title = title.strip()
        
        # Remove "Reuters:" prefix if present
        title = re.sub(r'^Reuters:\s*', '', title, flags=re.IGNORECASE)
        
        # Remove location prefixes like "LONDON -", "NEW YORK -"
        title = re.sub(r'^[A-Z\s]+\s*-\s*', '', title)
        
        # Clean HTML entities and tags
        title = self.clean_text(title)
        
        return title
    
    def clean_reuters_content(self, content: str) -> str:
        """Clean Reuters-specific content formatting.
        
        Args:
            content: Raw content text
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Clean HTML and normalize whitespace
        content = self.clean_text(content)
        
        # Remove common Reuters footer text
        footer_patterns = [
            r'Reporting by.*$',
            r'Additional reporting by.*$',
            r'Editing by.*$',
            r'\(Reporting by.*\)$',
            r'©.*Reuters.*$'
        ]
        
        for pattern in footer_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove location datelines at the beginning
        content = re.sub(r'^[A-Z\s]+,\s*[A-Za-z]+\s+\d+\s*\([A-Za-z]+\)\s*-\s*', '', content)
        
        return content.strip()
    
    def extract_reuters_author(self, entry) -> Optional[str]:
        """Extract author information from Reuters entry.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            Author name or None
        """
        # Try standard author field
        author = self.extract_field(entry, 'author')
        if author:
            return author
        
        # Try to extract from content
        content = self.extract_field(entry, 'summary', '')
        if content:
            # Look for Reuters reporting patterns
            author_patterns = [
                r'Reporting by\s+([^,\n]+)',
                r'By\s+([^,\n]+),?\s*Reuters',
                r'\(Reporting by\s+([^)]+)\)'
            ]
            
            for pattern in author_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    author_text = match.group(1).strip()
                    # Clean up author text
                    author_text = re.sub(r'\s+in\s+[A-Z\s]+$', '', author_text, flags=re.IGNORECASE)
                    return author_text
        
        return None
    
    def extract_reuters_categories(self, entry) -> list:
        """Extract categories from Reuters entry.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            List of categories
        """
        categories = self.extract_categories(entry)
        
        # Add Reuters-specific category detection from URL patterns
        link = self.extract_field(entry, 'link', '')
        if link:
            url_categories = {
                'Business': ['/business/', '/markets/', '/finance/'],
                'Technology': ['/technology/', '/tech/'],
                'Politics': ['/politics/', '/government/'],
                'World': ['/world/', '/international/'],
                'Sports': ['/sports/', '/sport/'],
                'Health': ['/health/', '/healthcare/'],
                'Environment': ['/environment/', '/climate/'],
                'Entertainment': ['/entertainment/', '/lifestyle/']
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
            'Markets': ['stock', 'market', 'trading', 'shares', 'index'],
            'Energy': ['oil', 'gas', 'energy', 'petroleum', 'crude'],
            'Currency': ['dollar', 'euro', 'currency', 'forex', 'exchange rate'],
            'Commodities': ['gold', 'silver', 'copper', 'commodity', 'metals'],
            'Earnings': ['earnings', 'profit', 'revenue', 'quarterly results']
        }
        
        for category, keywords in content_categories.items():
            if any(keyword in text_to_check for keyword in keywords):
                if category not in categories:
                    categories.append(category)
        
        return categories
    
    def get_field_alternatives(self):
        """Get alternative field names for Reuters RSS feeds."""
        return {
            'title': ['title'],
            'link': ['link', 'guid'],
            'summary': ['summary', 'description'],
            'content': ['summary', 'description'],
            'published_parsed': ['published_parsed', 'updated_parsed'],
            'author': ['author', 'dc_creator'],
            'category': ['category', 'tags']
        }
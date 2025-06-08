"""Kommersant RSS template for Kommersant.ru feeds."""

import re
from typing import Optional
from .base_template import RSSTemplate
from models.news_item import NewsItem


class KommersantRSSTemplate(RSSTemplate):
    """Template for Kommersant.ru RSS feeds."""
    
    def __init__(self, source_name: str = "Kommersant"):
        """Initialize the Kommersant RSS template."""
        super().__init__("kommersant", source_name)
    
    def parse_entry(self, entry) -> Optional[NewsItem]:
        """Parse a single Kommersant RSS entry into a NewsItem.
        
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
            
            # Clean Kommersant-specific formatting
            if title:
                title = self.clean_kommersant_title(title)
            
            if summary:
                summary = self.clean_kommersant_content(summary)
            
            # Parse published date
            published_at = None
            time_struct = self.extract_field(entry, 'published_parsed')
            if time_struct:
                published_at = self.parse_datetime(time_struct)
            
            # Extract Kommersant-specific fields
            author = self.extract_kommersant_author(entry)
            categories = self.extract_kommersant_categories(entry)
            
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
            self.logger.warning(f"Failed to parse Kommersant RSS entry: {e}")
            return None
    
    def validate_feed(self, feed) -> bool:
        """Validate if the feed is from Kommersant.
        
        Args:
            feed: Parsed feed from feedparser
            
        Returns:
            True if feed is from Kommersant
        """
        if not hasattr(feed, 'feed') or not hasattr(feed, 'entries'):
            return False
        
        # Check feed title or link for Kommersant indicators
        feed_info = feed.feed
        
        kommersant_indicators = [
            'kommersant',
            'коммерсант',
            'kommersant.ru'
        ]
        
        # Check feed title
        if hasattr(feed_info, 'title') and feed_info.title:
            title_lower = feed_info.title.lower()
            if any(indicator in title_lower for indicator in kommersant_indicators):
                return True
        
        # Check feed link
        if hasattr(feed_info, 'link') and feed_info.link:
            link_lower = feed_info.link.lower()
            if any(indicator in link_lower for indicator in kommersant_indicators):
                return True
        
        # Check entry links
        for entry in feed.entries[:3]:
            if hasattr(entry, 'link') and entry.link:
                link_lower = entry.link.lower()
                if 'kommersant.ru' in link_lower:
                    return True
        
        return False
    
    def clean_kommersant_title(self, title: str) -> str:
        """Clean Kommersant-specific title formatting.
        
        Args:
            title: Raw title text
            
        Returns:
            Cleaned title
        """
        if not title:
            return ""
        
        # Remove common Kommersant prefixes/suffixes
        title = title.strip()
        
        # Remove "Коммерсантъ:" prefix if present
        title = re.sub(r'^Коммерсантъ:\s*', '', title)
        
        # Clean HTML entities and tags
        title = self.clean_text(title)
        
        return title
    
    def clean_kommersant_content(self, content: str) -> str:
        """Clean Kommersant-specific content formatting.
        
        Args:
            content: Raw content text
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Clean HTML and normalize whitespace
        content = self.clean_text(content)
        
        # Remove common Kommersant footer text
        footer_patterns = [
            r'Читайте также.*$',
            r'Подробнее.*$',
            r'©.*Коммерсантъ.*$'
        ]
        
        for pattern in footer_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content.strip()
    
    def extract_kommersant_author(self, entry) -> Optional[str]:
        """Extract author information from Kommersant entry.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            Author name or None
        """
        # Try standard author field
        author = self.extract_field(entry, 'author')
        if author:
            return author
        
        # Try to extract from content or summary
        content = self.extract_field(entry, 'summary', '')
        if content:
            # Look for author patterns in Russian
            author_patterns = [
                r'Автор:\s*([^,\n]+)',
                r'([А-Я][а-я]+\s+[А-Я][а-я]+),?\s*корреспондент',
                r'([А-Я][а-я]+\s+[А-Я][а-я]+),?\s*обозреватель'
            ]
            
            for pattern in author_patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1).strip()
        
        return None
    
    def extract_kommersant_categories(self, entry) -> list:
        """Extract categories from Kommersant entry.
        
        Args:
            entry: RSS entry from feedparser
            
        Returns:
            List of categories
        """
        categories = self.extract_categories(entry)
        
        # Add Kommersant-specific category detection
        title = self.extract_field(entry, 'title', '')
        content = self.extract_field(entry, 'summary', '')
        
        # Detect categories from content patterns
        category_patterns = {
            'Политика': [r'политик', r'правительств', r'президент', r'министр'],
            'Экономика': [r'экономик', r'финанс', r'банк', r'рубл', r'доллар'],
            'Бизнес': [r'компани', r'бизнес', r'корпораци', r'акци'],
            'Международные': [r'США', r'Европ', r'Китай', r'международн'],
            'Спорт': [r'спорт', r'футбол', r'хоккей', r'олимпиад']
        }
        
        text_to_check = f"{title} {content}".lower()
        
        for category, patterns in category_patterns.items():
            if any(re.search(pattern, text_to_check) for pattern in patterns):
                if category not in categories:
                    categories.append(category)
        
        return categories
    
    def get_field_alternatives(self):
        """Get alternative field names for Kommersant RSS feeds."""
        return {
            'title': ['title'],
            'link': ['link', 'guid'],
            'summary': ['summary', 'description'],
            'content': ['summary', 'description'],
            'published_parsed': ['published_parsed', 'updated_parsed'],
            'author': ['author', 'dc_creator'],
            'category': ['category', 'tags']
        }
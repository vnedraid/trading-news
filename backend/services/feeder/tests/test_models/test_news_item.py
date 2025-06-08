"""Tests for the NewsItem model."""

import pytest
from datetime import datetime
from src.models.news_item import NewsItem


class TestNewsItem:
    """Test cases for NewsItem model."""
    
    def test_news_item_creation(self, sample_news_item):
        """Test basic NewsItem creation."""
        assert sample_news_item.title == "Test News Article"
        assert sample_news_item.source_name == "Test Source"
        assert sample_news_item.source_type == "rss"
        assert sample_news_item.author == "Test Author"
        assert len(sample_news_item.categories) == 2
        assert "technology" in sample_news_item.categories
        assert len(sample_news_item.media_urls) == 1
    
    def test_content_hash_generation(self):
        """Test that content hash is generated automatically."""
        news_item = NewsItem(
            title="Test Article",
            description="Test description",
            link="https://example.com/test",
            publication_date=datetime(2024, 1, 1, 12, 0, 0),
            source_name="Test Source",
            source_type="rss"
        )
        
        assert news_item.content_hash != ""
        assert len(news_item.content_hash) == 64  # SHA-256 hex length
    
    def test_content_hash_consistency(self):
        """Test that same content produces same hash."""
        news_item1 = NewsItem(
            title="Test Article",
            description="Test description",
            link="https://example.com/test",
            publication_date=datetime(2024, 1, 1, 12, 0, 0),
            source_name="Test Source",
            source_type="rss"
        )
        
        news_item2 = NewsItem(
            title="Test Article",
            description="Different description",  # Different description
            link="https://example.com/test",
            publication_date=datetime(2024, 1, 1, 12, 0, 0),
            source_name="Test Source",
            source_type="rss"
        )
        
        # Hash should be the same because it's based on title, link, and date
        assert news_item1.content_hash == news_item2.content_hash
    
    def test_content_hash_different_for_different_content(self):
        """Test that different content produces different hash."""
        news_item1 = NewsItem(
            title="Test Article",
            description="Test description",
            link="https://example.com/test",
            publication_date=datetime(2024, 1, 1, 12, 0, 0),
            source_name="Test Source",
            source_type="rss"
        )
        
        news_item2 = NewsItem(
            title="Different Article",  # Different title
            description="Test description",
            link="https://example.com/test",
            publication_date=datetime(2024, 1, 1, 12, 0, 0),
            source_name="Test Source",
            source_type="rss"
        )
        
        assert news_item1.content_hash != news_item2.content_hash
    
    def test_to_dict_conversion(self, sample_news_item):
        """Test conversion to dictionary."""
        data = sample_news_item.to_dict()
        
        assert isinstance(data, dict)
        assert data["title"] == sample_news_item.title
        assert data["source_name"] == sample_news_item.source_name
        assert data["source_type"] == sample_news_item.source_type
        assert data["content_hash"] == sample_news_item.content_hash
        assert isinstance(data["publication_date"], str)  # Should be ISO format
        assert isinstance(data["extracted_at"], str)  # Should be ISO format
        assert isinstance(data["categories"], list)
        assert isinstance(data["media_urls"], list)
    
    def test_from_dict_creation(self, sample_news_item):
        """Test creation from dictionary."""
        data = sample_news_item.to_dict()
        recreated_item = NewsItem.from_dict(data)
        
        assert recreated_item.title == sample_news_item.title
        assert recreated_item.description == sample_news_item.description
        assert recreated_item.link == sample_news_item.link
        assert recreated_item.source_name == sample_news_item.source_name
        assert recreated_item.source_type == sample_news_item.source_type
        assert recreated_item.author == sample_news_item.author
        assert recreated_item.categories == sample_news_item.categories
        assert recreated_item.full_content == sample_news_item.full_content
        assert recreated_item.media_urls == sample_news_item.media_urls
        assert recreated_item.content_hash == sample_news_item.content_hash
        # Note: publication_date and extracted_at might have slight differences due to serialization
    
    def test_round_trip_serialization(self, sample_news_item):
        """Test that serialization and deserialization preserves data."""
        data = sample_news_item.to_dict()
        recreated_item = NewsItem.from_dict(data)
        recreated_data = recreated_item.to_dict()
        
        # Should be identical after round trip
        assert data == recreated_data
    
    def test_is_valid_with_valid_item(self, sample_news_item):
        """Test validation with valid news item."""
        assert sample_news_item.is_valid() is True
    
    def test_is_valid_with_missing_title(self):
        """Test validation with missing title."""
        news_item = NewsItem(
            title="",  # Empty title
            description="Test description",
            link="https://example.com/test",
            publication_date=datetime.now(),
            source_name="Test Source",
            source_type="rss"
        )
        
        assert news_item.is_valid() is False
    
    def test_is_valid_with_missing_link(self):
        """Test validation with missing link."""
        news_item = NewsItem(
            title="Test Article",
            description="Test description",
            link="",  # Empty link
            publication_date=datetime.now(),
            source_name="Test Source",
            source_type="rss"
        )
        
        assert news_item.is_valid() is False
    
    def test_is_valid_with_missing_source_name(self):
        """Test validation with missing source name."""
        news_item = NewsItem(
            title="Test Article",
            description="Test description",
            link="https://example.com/test",
            publication_date=datetime.now(),
            source_name="",  # Empty source name
            source_type="rss"
        )
        
        assert news_item.is_valid() is False
    
    def test_string_representation(self, sample_news_item):
        """Test string representation."""
        str_repr = str(sample_news_item)
        assert "NewsItem" in str_repr
        assert "Test News Article" in str_repr
        assert "Test Source" in str_repr
    
    def test_repr_representation(self, sample_news_item):
        """Test detailed representation."""
        repr_str = repr(sample_news_item)
        assert "NewsItem(" in repr_str
        assert "title='Test News Article'" in repr_str
        assert "source_name='Test Source'" in repr_str
        assert "source_type='rss'" in repr_str
        assert f"content_hash='{sample_news_item.content_hash}'" in repr_str
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        news_item = NewsItem(
            title="Test Article",
            description="Test description",
            link="https://example.com/test",
            publication_date=datetime.now(),
            source_name="Test Source",
            source_type="rss"
        )
        
        assert news_item.author is None
        assert news_item.categories == []
        assert news_item.full_content is None
        assert news_item.media_urls == []
        assert news_item.content_hash != ""
        assert isinstance(news_item.extracted_at, datetime)
        assert news_item.raw_data == {}
    
    def test_manual_content_hash(self):
        """Test that manually set content hash is preserved."""
        custom_hash = "custom_hash_value"
        news_item = NewsItem(
            title="Test Article",
            description="Test description",
            link="https://example.com/test",
            publication_date=datetime.now(),
            source_name="Test Source",
            source_type="rss",
            content_hash=custom_hash
        )
        
        assert news_item.content_hash == custom_hash
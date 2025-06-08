"""Tests for data models."""

import pytest
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.news_item import NewsItem
from models.worker_config import WorkerConfig, RSSWorkerConfig


class TestNewsItem:
    """Test cases for NewsItem model."""

    def test_news_item_creation_with_required_fields(self):
        """Test creating a NewsItem with only required fields."""
        news_item = NewsItem(
            title="Test News Title",
            url="https://example.com/news/1",
            source="test_source"
        )
        
        assert news_item.title == "Test News Title"
        assert news_item.url == "https://example.com/news/1"
        assert news_item.source == "test_source"
        assert news_item.content is None
        assert news_item.summary is None
        assert news_item.published_at is None
        assert isinstance(news_item.created_at, datetime)
        assert news_item.tags == []

    def test_news_item_creation_with_all_fields(self):
        """Test creating a NewsItem with all fields."""
        published_at = datetime(2023, 1, 1, 12, 0, 0)
        created_at = datetime(2023, 1, 1, 12, 5, 0)
        
        news_item = NewsItem(
            title="Full News Title",
            url="https://example.com/news/2",
            source="full_source",
            content="Full news content here",
            summary="News summary",
            published_at=published_at,
            created_at=created_at,
            tags=["finance", "trading"]
        )
        
        assert news_item.title == "Full News Title"
        assert news_item.url == "https://example.com/news/2"
        assert news_item.source == "full_source"
        assert news_item.content == "Full news content here"
        assert news_item.summary == "News summary"
        assert news_item.published_at == published_at
        assert news_item.created_at == created_at
        assert news_item.tags == ["finance", "trading"]

    def test_news_item_validation_empty_title(self):
        """Test that empty title raises validation error."""
        with pytest.raises(ValueError, match="Title cannot be empty"):
            NewsItem(
                title="",
                url="https://example.com/news/1",
                source="test_source"
            )

    def test_news_item_validation_empty_url(self):
        """Test that empty URL raises validation error."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            NewsItem(
                title="Test Title",
                url="",
                source="test_source"
            )

    def test_news_item_validation_invalid_url(self):
        """Test that invalid URL raises validation error."""
        with pytest.raises(ValueError, match="Invalid URL format"):
            NewsItem(
                title="Test Title",
                url="not-a-valid-url",
                source="test_source"
            )

    def test_news_item_validation_empty_source(self):
        """Test that empty source raises validation error."""
        with pytest.raises(ValueError, match="Source cannot be empty"):
            NewsItem(
                title="Test Title",
                url="https://example.com/news/1",
                source=""
            )

    def test_news_item_to_dict(self):
        """Test converting NewsItem to dictionary."""
        news_item = NewsItem(
            title="Test Title",
            url="https://example.com/news/1",
            source="test_source",
            content="Test content",
            tags=["tag1", "tag2"]
        )
        
        result = news_item.to_dict()
        
        assert result["title"] == "Test Title"
        assert result["url"] == "https://example.com/news/1"
        assert result["source"] == "test_source"
        assert result["content"] == "Test content"
        assert result["tags"] == ["tag1", "tag2"]
        assert "created_at" in result
        assert isinstance(result["created_at"], str)  # Should be ISO format string

    def test_news_item_from_dict(self):
        """Test creating NewsItem from dictionary."""
        data = {
            "title": "Test Title",
            "url": "https://example.com/news/1",
            "source": "test_source",
            "content": "Test content",
            "tags": ["tag1", "tag2"],
            "created_at": "2023-01-01T12:00:00"
        }
        
        news_item = NewsItem.from_dict(data)
        
        assert news_item.title == "Test Title"
        assert news_item.url == "https://example.com/news/1"
        assert news_item.source == "test_source"
        assert news_item.content == "Test content"
        assert news_item.tags == ["tag1", "tag2"]


class TestWorkerConfig:
    """Test cases for WorkerConfig model."""

    def test_worker_config_creation(self):
        """Test creating a basic WorkerConfig."""
        config = WorkerConfig(
            name="test_worker",
            type="rss",
            worker_id="test_001"
        )
        
        assert config.name == "test_worker"
        assert config.type == "rss"
        assert config.worker_id == "test_001"
        assert config.enabled is True

    def test_worker_config_validation_empty_name(self):
        """Test that empty name raises validation error."""
        with pytest.raises(ValueError, match="Name cannot be empty"):
            WorkerConfig(
                name="",
                type="rss",
                worker_id="test_001"
            )

    def test_worker_config_validation_invalid_type(self):
        """Test that invalid type raises validation error."""
        with pytest.raises(ValueError, match="Invalid worker type"):
            WorkerConfig(
                name="test_worker",
                type="invalid_type",
                worker_id="test_001"
            )

    def test_worker_config_validation_empty_worker_id(self):
        """Test that empty worker_id raises validation error."""
        with pytest.raises(ValueError, match="Worker ID cannot be empty"):
            WorkerConfig(
                name="test_worker",
                type="rss",
                worker_id=""
            )


class TestRSSWorkerConfig:
    """Test cases for RSSWorkerConfig model."""

    def test_rss_worker_config_creation(self):
        """Test creating an RSSWorkerConfig."""
        config = RSSWorkerConfig(
            name="rss_worker",
            worker_id="rss_001",
            url="https://example.com/rss.xml",
            polling_interval="5m"
        )
        
        assert config.name == "rss_worker"
        assert config.type == "rss"
        assert config.worker_id == "rss_001"
        assert config.url == "https://example.com/rss.xml"
        assert config.polling_interval == "5m"
        assert config.timeout == "30s"  # default value
        assert config.max_retries == 3  # default value

    def test_rss_worker_config_with_custom_values(self):
        """Test creating RSSWorkerConfig with custom timeout and retries."""
        config = RSSWorkerConfig(
            name="custom_rss_worker",
            worker_id="rss_002",
            url="https://example.com/custom.xml",
            polling_interval="10m",
            timeout="60s",
            max_retries=5
        )
        
        assert config.timeout == "60s"
        assert config.max_retries == 5

    def test_rss_worker_config_validation_empty_url(self):
        """Test that empty URL raises validation error."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            RSSWorkerConfig(
                name="rss_worker",
                worker_id="rss_001",
                url="",
                polling_interval="5m"
            )

    def test_rss_worker_config_validation_invalid_url(self):
        """Test that invalid URL raises validation error."""
        with pytest.raises(ValueError, match="Invalid URL format"):
            RSSWorkerConfig(
                name="rss_worker",
                worker_id="rss_001",
                url="not-a-valid-url",
                polling_interval="5m"
            )

    def test_rss_worker_config_validation_invalid_polling_interval(self):
        """Test that invalid polling interval raises validation error."""
        with pytest.raises(ValueError, match="Invalid polling interval format"):
            RSSWorkerConfig(
                name="rss_worker",
                worker_id="rss_001",
                url="https://example.com/rss.xml",
                polling_interval="invalid"
            )

    def test_rss_worker_config_validation_invalid_timeout(self):
        """Test that invalid timeout raises validation error."""
        with pytest.raises(ValueError, match="Invalid timeout format"):
            RSSWorkerConfig(
                name="rss_worker",
                worker_id="rss_001",
                url="https://example.com/rss.xml",
                polling_interval="5m",
                timeout="invalid"
            )

    def test_rss_worker_config_validation_negative_retries(self):
        """Test that negative max_retries raises validation error."""
        with pytest.raises(ValueError, match="Max retries must be non-negative"):
            RSSWorkerConfig(
                name="rss_worker",
                worker_id="rss_001",
                url="https://example.com/rss.xml",
                polling_interval="5m",
                max_retries=-1
            )
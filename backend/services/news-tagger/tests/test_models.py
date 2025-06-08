"""Tests for data models."""

import pytest
from datetime import datetime, timezone
from typing import List, Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models.news_item import NewsItem, TaggedNewsItem
from models.tagger_config import TaggerConfig, LLMConfig


class TestNewsItem:
    """Test cases for NewsItem model (shared from news-feeder)."""

    def test_news_item_creation(self):
        """Test creating a NewsItem."""
        news_item = NewsItem(
            title="Test News Title",
            url="https://example.com/news/1",
            source="test_source",
            content="Test news content",
            summary="Test summary"
        )
        
        assert news_item.title == "Test News Title"
        assert news_item.url == "https://example.com/news/1"
        assert news_item.source == "test_source"
        assert news_item.content == "Test news content"
        assert news_item.summary == "Test summary"
        assert isinstance(news_item.created_at, datetime)
        assert news_item.tags == []


class TestTaggedNewsItem:
    """Test cases for TaggedNewsItem model."""

    def test_tagged_news_item_creation_from_news_item(self):
        """Test creating TaggedNewsItem from NewsItem."""
        original_item = NewsItem(
            title="Test News",
            url="https://example.com/news/1",
            source="test_source",
            content="Financial markets are volatile today"
        )
        
        tags = ["finance", "markets", "trading"]
        confidence_scores = {"finance": 0.95, "markets": 0.87, "trading": 0.72}
        
        tagged_item = TaggedNewsItem.from_news_item(
            original_item,
            tags=tags,
            confidence_scores=confidence_scores,
            model_used="gpt-4"
        )
        
        # Check inherited properties
        assert tagged_item.title == original_item.title
        assert tagged_item.url == original_item.url
        assert tagged_item.source == original_item.source
        assert tagged_item.content == original_item.content
        assert tagged_item.created_at == original_item.created_at
        
        # Check new properties
        assert tagged_item.tags == tags
        assert tagged_item.confidence_scores == confidence_scores
        assert tagged_item.model_used == "gpt-4"
        assert isinstance(tagged_item.tagged_at, datetime)

    def test_tagged_news_item_creation_direct(self):
        """Test creating TaggedNewsItem directly."""
        tagged_at = datetime.now(timezone.utc)
        
        tagged_item = TaggedNewsItem(
            title="Direct Test News",
            url="https://example.com/news/2",
            source="direct_source",
            content="Technology stocks surge",
            tags=["technology", "stocks"],
            confidence_scores={"technology": 0.92, "stocks": 0.88},
            model_used="claude-3",
            tagged_at=tagged_at
        )
        
        assert tagged_item.title == "Direct Test News"
        assert tagged_item.tags == ["technology", "stocks"]
        assert tagged_item.confidence_scores == {"technology": 0.92, "stocks": 0.88}
        assert tagged_item.model_used == "claude-3"
        assert tagged_item.tagged_at == tagged_at

    def test_tagged_news_item_validation_empty_tags(self):
        """Test that empty tags list is allowed."""
        tagged_item = TaggedNewsItem(
            title="Test News",
            url="https://example.com/news/1",
            source="test_source",
            tags=[],
            model_used="gpt-4"
        )
        
        assert tagged_item.tags == []
        assert tagged_item.confidence_scores == {}

    def test_tagged_news_item_validation_mismatched_scores(self):
        """Test validation when confidence scores don't match tags."""
        with pytest.raises(ValueError, match="Confidence scores must match tags"):
            TaggedNewsItem(
                title="Test News",
                url="https://example.com/news/1",
                source="test_source",
                tags=["finance", "markets"],
                confidence_scores={"finance": 0.95},  # Missing "markets"
                model_used="gpt-4"
            )

    def test_tagged_news_item_validation_invalid_confidence_score(self):
        """Test validation of confidence score range."""
        with pytest.raises(ValueError, match="Confidence scores must be between 0 and 1"):
            TaggedNewsItem(
                title="Test News",
                url="https://example.com/news/1",
                source="test_source",
                tags=["finance"],
                confidence_scores={"finance": 1.5},  # Invalid score > 1
                model_used="gpt-4"
            )

    def test_tagged_news_item_validation_empty_model(self):
        """Test that empty model_used raises validation error."""
        with pytest.raises(ValueError, match="Model used cannot be empty"):
            TaggedNewsItem(
                title="Test News",
                url="https://example.com/news/1",
                source="test_source",
                tags=["finance"],
                model_used=""
            )

    def test_tagged_news_item_to_dict(self):
        """Test converting TaggedNewsItem to dictionary."""
        tagged_item = TaggedNewsItem(
            title="Test News",
            url="https://example.com/news/1",
            source="test_source",
            content="Test content",
            tags=["finance", "markets"],
            confidence_scores={"finance": 0.95, "markets": 0.87},
            model_used="gpt-4"
        )
        
        result = tagged_item.to_dict()
        
        assert result["title"] == "Test News"
        assert result["url"] == "https://example.com/news/1"
        assert result["source"] == "test_source"
        assert result["content"] == "Test content"
        assert result["tags"] == ["finance", "markets"]
        assert result["confidence_scores"] == {"finance": 0.95, "markets": 0.87}
        assert result["model_used"] == "gpt-4"
        assert "created_at" in result
        assert "tagged_at" in result

    def test_tagged_news_item_from_dict(self):
        """Test creating TaggedNewsItem from dictionary."""
        data = {
            "title": "Test News",
            "url": "https://example.com/news/1",
            "source": "test_source",
            "content": "Test content",
            "tags": ["finance", "markets"],
            "confidence_scores": {"finance": 0.95, "markets": 0.87},
            "model_used": "gpt-4",
            "created_at": "2023-01-01T12:00:00+00:00",
            "tagged_at": "2023-01-01T12:05:00+00:00"
        }
        
        tagged_item = TaggedNewsItem.from_dict(data)
        
        assert tagged_item.title == "Test News"
        assert tagged_item.tags == ["finance", "markets"]
        assert tagged_item.confidence_scores == {"finance": 0.95, "markets": 0.87}
        assert tagged_item.model_used == "gpt-4"


class TestLLMConfig:
    """Test cases for LLMConfig model."""

    def test_llm_config_creation_with_defaults(self):
        """Test creating LLMConfig with default values."""
        config = LLMConfig(
            api_key="test-key",
            model="gpt-4"
        )
        
        assert config.provider == "openrouter"
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.base_url == "https://openrouter.ai/api/v1"
        assert config.max_tokens == 150
        assert config.temperature == 0.3
        assert config.timeout == 30.0

    def test_llm_config_creation_with_custom_values(self):
        """Test creating LLMConfig with custom values."""
        config = LLMConfig(
            provider="openai",
            api_key="custom-key",
            model="gpt-3.5-turbo",
            base_url="https://api.openai.com/v1",
            max_tokens=200,
            temperature=0.7,
            timeout=60.0
        )
        
        assert config.provider == "openai"
        assert config.api_key == "custom-key"
        assert config.model == "gpt-3.5-turbo"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.max_tokens == 200
        assert config.temperature == 0.7
        assert config.timeout == 60.0

    def test_llm_config_validation_empty_api_key(self):
        """Test that empty API key raises validation error."""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            LLMConfig(
                api_key="",
                model="gpt-4"
            )

    def test_llm_config_validation_empty_model(self):
        """Test that empty model raises validation error."""
        with pytest.raises(ValueError, match="Model cannot be empty"):
            LLMConfig(
                api_key="test-key",
                model=""
            )

    def test_llm_config_validation_invalid_temperature(self):
        """Test that invalid temperature raises validation error."""
        with pytest.raises(ValueError, match="Temperature must be between 0 and 2"):
            LLMConfig(
                api_key="test-key",
                model="gpt-4",
                temperature=2.5
            )

    def test_llm_config_validation_invalid_max_tokens(self):
        """Test that invalid max_tokens raises validation error."""
        with pytest.raises(ValueError, match="Max tokens must be positive"):
            LLMConfig(
                api_key="test-key",
                model="gpt-4",
                max_tokens=0
            )


class TestTaggerConfig:
    """Test cases for TaggerConfig model."""

    def test_tagger_config_creation_with_defaults(self):
        """Test creating TaggerConfig with default values."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        config = TaggerConfig(llm=llm_config)
        
        assert config.llm == llm_config
        assert config.max_tags == 5
        assert config.min_confidence == 0.5
        assert "finance" in config.categories
        assert "trading" in config.categories
        assert "markets" in config.categories

    def test_tagger_config_creation_with_custom_values(self):
        """Test creating TaggerConfig with custom values."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        custom_categories = ["tech", "politics", "sports"]
        
        config = TaggerConfig(
            llm=llm_config,
            max_tags=3,
            min_confidence=0.7,
            categories=custom_categories
        )
        
        assert config.max_tags == 3
        assert config.min_confidence == 0.7
        assert config.categories == custom_categories

    def test_tagger_config_validation_invalid_max_tags(self):
        """Test that invalid max_tags raises validation error."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        
        with pytest.raises(ValueError, match="Max tags must be positive"):
            TaggerConfig(
                llm=llm_config,
                max_tags=0
            )

    def test_tagger_config_validation_invalid_min_confidence(self):
        """Test that invalid min_confidence raises validation error."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        
        with pytest.raises(ValueError, match="Min confidence must be between 0 and 1"):
            TaggerConfig(
                llm=llm_config,
                min_confidence=1.5
            )

    def test_tagger_config_validation_empty_categories(self):
        """Test that empty categories raises validation error."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        
        with pytest.raises(ValueError, match="Categories cannot be empty"):
            TaggerConfig(
                llm=llm_config,
                categories=[]
            )
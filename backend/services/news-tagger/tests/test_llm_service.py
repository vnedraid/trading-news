"""Tests for LLM service integration."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from services.llm_service import LLMService, TaggingResult
from models.news_item import NewsItem
from models.tagger_config import LLMConfig, TaggerConfig


class TestTaggingResult:
    """Test cases for TaggingResult model."""

    def test_tagging_result_creation(self):
        """Test creating a TaggingResult."""
        result = TaggingResult(
            tags=["finance", "markets"],
            confidence_scores={"finance": 0.95, "markets": 0.87},
            model_used="gpt-4",
            raw_response="Raw LLM response"
        )
        
        assert result.tags == ["finance", "markets"]
        assert result.confidence_scores == {"finance": 0.95, "markets": 0.87}
        assert result.model_used == "gpt-4"
        assert result.raw_response == "Raw LLM response"

    def test_tagging_result_validation_mismatched_scores(self):
        """Test validation when confidence scores don't match tags."""
        with pytest.raises(ValueError, match="Confidence scores must match tags"):
            TaggingResult(
                tags=["finance", "markets"],
                confidence_scores={"finance": 0.95},  # Missing "markets"
                model_used="gpt-4"
            )

    def test_tagging_result_validation_invalid_confidence_score(self):
        """Test validation of confidence score range."""
        with pytest.raises(ValueError, match="Confidence scores must be between 0 and 1"):
            TaggingResult(
                tags=["finance"],
                confidence_scores={"finance": 1.5},  # Invalid score > 1
                model_used="gpt-4"
            )


class TestLLMService:
    """Test cases for LLMService."""

    def test_llm_service_creation(self):
        """Test creating an LLMService."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        
        service = LLMService(tagger_config)
        
        assert service.config == tagger_config
        assert service.client is not None

    @pytest.mark.asyncio
    async def test_tag_news_success(self):
        """Test successful news tagging."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        news_item = NewsItem(
            title="Stock Market Surges on Fed Decision",
            url="https://example.com/news/1",
            source="test_source",
            content="The stock market rallied today after the Federal Reserve announced..."
        )
        
        # Mock OpenAI client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "tags": ["finance", "markets", "federal-reserve"],
            "confidence_scores": {
                "finance": 0.95,
                "markets": 0.87,
                "federal-reserve": 0.82
            }
        })
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response) as mock_create:
            result = await service.tag_news(news_item)
            
            # Verify the result
            assert isinstance(result, TaggingResult)
            assert result.tags == ["finance", "markets", "federal-reserve"]
            assert result.confidence_scores == {
                "finance": 0.95,
                "markets": 0.87,
                "federal-reserve": 0.82
            }
            assert result.model_used == "gpt-4"
            
            # Verify the API call
            mock_create.assert_called_once()
            call_args = mock_create.call_args
            assert call_args[1]["model"] == "gpt-4"
            assert call_args[1]["max_tokens"] == 150
            assert call_args[1]["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_tag_news_with_content_only(self):
        """Test tagging news with content but no title."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        news_item = NewsItem(
            title="Crypto News",
            url="https://example.com/news/1",
            source="test_source",
            content="Cryptocurrency prices are volatile today due to regulatory concerns."
        )
        
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "tags": ["cryptocurrency", "regulation"],
            "confidence_scores": {
                "cryptocurrency": 0.92,
                "regulation": 0.78
            }
        })
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            result = await service.tag_news(news_item)
            
            assert result.tags == ["cryptocurrency", "regulation"]

    @pytest.mark.asyncio
    async def test_tag_news_empty_content(self):
        """Test tagging news with empty content."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        news_item = NewsItem(
            title="Empty Content News",
            url="https://example.com/news/1",
            source="test_source",
            content=""
        )
        
        with pytest.raises(ValueError, match="No content available for tagging"):
            await service.tag_news(news_item)

    @pytest.mark.asyncio
    async def test_tag_news_api_error(self):
        """Test handling of API errors."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        news_item = NewsItem(
            title="Test News",
            url="https://example.com/news/1",
            source="test_source",
            content="Test content"
        )
        
        with patch.object(service.client.chat.completions, 'create', side_effect=Exception("API Error")):
            with pytest.raises(Exception, match="API Error"):
                await service.tag_news(news_item)

    @pytest.mark.asyncio
    async def test_tag_news_invalid_json_response(self):
        """Test handling of invalid JSON response."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        news_item = NewsItem(
            title="Test News",
            url="https://example.com/news/1",
            source="test_source",
            content="Test content"
        )
        
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            with pytest.raises(ValueError, match="Failed to parse LLM response"):
                await service.tag_news(news_item)

    @pytest.mark.asyncio
    async def test_tag_news_confidence_filtering(self):
        """Test filtering tags by confidence threshold."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config, min_confidence=0.8)
        service = LLMService(tagger_config)
        
        news_item = NewsItem(
            title="Test News",
            url="https://example.com/news/1",
            source="test_source",
            content="Test content"
        )
        
        # Mock response with mixed confidence scores
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "tags": ["finance", "markets", "technology"],
            "confidence_scores": {
                "finance": 0.95,  # Above threshold
                "markets": 0.75,  # Below threshold
                "technology": 0.85  # Above threshold
            }
        })
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            result = await service.tag_news(news_item)
            
            # Should only include tags above confidence threshold
            assert result.tags == ["finance", "technology"]
            assert result.confidence_scores == {
                "finance": 0.95,
                "technology": 0.85
            }

    @pytest.mark.asyncio
    async def test_tag_news_max_tags_limit(self):
        """Test limiting number of tags returned."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config, max_tags=2)
        service = LLMService(tagger_config)
        
        news_item = NewsItem(
            title="Test News",
            url="https://example.com/news/1",
            source="test_source",
            content="Test content"
        )
        
        # Mock response with more tags than limit
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = json.dumps({
            "tags": ["finance", "markets", "technology", "politics"],
            "confidence_scores": {
                "finance": 0.95,
                "markets": 0.87,
                "technology": 0.82,
                "politics": 0.75
            }
        })
        
        with patch.object(service.client.chat.completions, 'create', return_value=mock_response):
            result = await service.tag_news(news_item)
            
            # Should only include top 2 tags by confidence
            assert len(result.tags) == 2
            assert result.tags == ["finance", "markets"]
            assert result.confidence_scores == {
                "finance": 0.95,
                "markets": 0.87
            }

    def test_build_prompt(self):
        """Test building the prompt for LLM."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        news_item = NewsItem(
            title="Stock Market News",
            url="https://example.com/news/1",
            source="test_source",
            content="The stock market rallied today..."
        )
        
        prompt = service._build_prompt(news_item)
        
        assert "Stock Market News" in prompt
        assert "The stock market rallied today..." in prompt
        assert "finance" in prompt  # Should include categories
        assert "trading" in prompt
        assert "JSON" in prompt  # Should mention JSON format

    def test_parse_llm_response_success(self):
        """Test parsing successful LLM response."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        response_content = json.dumps({
            "tags": ["finance", "markets"],
            "confidence_scores": {
                "finance": 0.95,
                "markets": 0.87
            }
        })
        
        result = service._parse_llm_response(response_content, "gpt-4")
        
        assert isinstance(result, TaggingResult)
        assert result.tags == ["finance", "markets"]
        assert result.confidence_scores == {"finance": 0.95, "markets": 0.87}
        assert result.model_used == "gpt-4"

    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        with pytest.raises(ValueError, match="Failed to parse LLM response"):
            service._parse_llm_response("Invalid JSON", "gpt-4")

    def test_parse_llm_response_missing_fields(self):
        """Test parsing response with missing required fields."""
        llm_config = LLMConfig(api_key="test-key", model="gpt-4")
        tagger_config = TaggerConfig(llm=llm_config)
        service = LLMService(tagger_config)
        
        response_content = json.dumps({
            "tags": ["finance"]
            # Missing confidence_scores
        })
        
        with pytest.raises(ValueError, match="Missing required fields in LLM response"):
            service._parse_llm_response(response_content, "gpt-4")
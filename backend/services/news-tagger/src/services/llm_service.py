"""LLM service for news tagging using OpenAI-compatible APIs."""

import json
import asyncio
from typing import List, Dict, Any
from openai import OpenAI

from models.news_item import NewsItem
from models.tagger_config import TaggerConfig


class TaggingResult:
    """Result of LLM tagging operation."""

    def __init__(
        self,
        tags: List[str],
        confidence_scores: Dict[str, float],
        model_used: str,
        raw_response: str = ""
    ):
        """Initialize TaggingResult.
        
        Args:
            tags: List of generated tags
            confidence_scores: Confidence scores for each tag
            model_used: The LLM model used
            raw_response: Raw response from LLM
        """
        self.tags = tags
        self.confidence_scores = confidence_scores
        self.model_used = model_used
        self.raw_response = raw_response
        
        self._validate_confidence_scores()

    def _validate_confidence_scores(self) -> None:
        """Validate confidence scores match tags and are in valid range."""
        if self.tags and self.confidence_scores:
            # Check that all tags have confidence scores
            if set(self.tags) != set(self.confidence_scores.keys()):
                raise ValueError("Confidence scores must match tags")
            
            # Check that all scores are in valid range [0, 1]
            for tag, score in self.confidence_scores.items():
                if not (0 <= score <= 1):
                    raise ValueError("Confidence scores must be between 0 and 1")


class LLMService:
    """Service for tagging news using LLM APIs."""

    def __init__(self, config: TaggerConfig):
        """Initialize LLM service.
        
        Args:
            config: Tagger configuration including LLM settings
        """
        self.config = config
        self.client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url
        )

    async def tag_news(self, news_item: NewsItem) -> TaggingResult:
        """Tag a news item using LLM.
        
        Args:
            news_item: News item to tag
            
        Returns:
            TaggingResult with generated tags and confidence scores
            
        Raises:
            ValueError: If no content available for tagging
            Exception: If LLM API call fails
        """
        # Check if we have meaningful content for analysis
        has_content = (news_item.content and news_item.content.strip()) or \
                     (hasattr(news_item, 'summary') and news_item.summary and news_item.summary.strip())
        
        if not has_content:
            raise ValueError("No content available for tagging")
        
        # Build prompt
        prompt = self._build_prompt(news_item)
        
        # Call LLM API
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial news tagging expert. Analyze news content and provide relevant tags with confidence scores."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature,
                timeout=self.config.llm.timeout
            )
            
            # Parse response
            response_content = response.choices[0].message.content
            result = self._parse_llm_response(response_content, self.config.llm.model)
            
            # Apply filtering
            filtered_result = self._apply_filters(result)
            
            return filtered_result
            
        except Exception as e:
            raise e

    def _extract_content(self, news_item: NewsItem) -> str:
        """Extract content for analysis from news item.
        
        Args:
            news_item: News item
            
        Returns:
            Combined content string
        """
        content_parts = []
        
        if news_item.title and news_item.title.strip():
            content_parts.append(f"Title: {news_item.title}")
        
        if news_item.content and news_item.content.strip():
            content_parts.append(f"Content: {news_item.content}")
        elif hasattr(news_item, 'summary') and news_item.summary and news_item.summary.strip():
            content_parts.append(f"Summary: {news_item.summary}")
        
        return "\n".join(content_parts)

    def _build_prompt(self, news_item: NewsItem) -> str:
        """Build prompt for LLM tagging.
        
        Args:
            news_item: News item to tag
            
        Returns:
            Formatted prompt string
        """
        content = self._extract_content(news_item)
        categories = ", ".join(self.config.categories)
        
        prompt = f"""
Analyze the following news content and generate relevant tags from the provided categories.

News Content:
{content}

Available Categories:
{categories}

Instructions:
1. Select the most relevant tags from the available categories
2. Provide confidence scores between 0 and 1 for each tag
3. Focus on financial, trading, and market-related aspects
4. Return response in JSON format with "tags" and "confidence_scores" fields

Example Response:
{{
    "tags": ["finance", "markets", "trading"],
    "confidence_scores": {{
        "finance": 0.95,
        "markets": 0.87,
        "trading": 0.72
    }}
}}

Response:
"""
        return prompt.strip()

    def _parse_llm_response(self, response_content: str, model_used: str) -> TaggingResult:
        """Parse LLM response into TaggingResult.
        
        Args:
            response_content: Raw response content from LLM
            model_used: Model that generated the response
            
        Returns:
            TaggingResult object
            
        Raises:
            ValueError: If response cannot be parsed or is invalid
        """
        try:
            # Parse JSON response
            data = json.loads(response_content)
            
            # Validate required fields
            if "tags" not in data or "confidence_scores" not in data:
                raise ValueError("Missing required fields in LLM response: tags, confidence_scores")
            
            tags = data["tags"]
            confidence_scores = data["confidence_scores"]
            
            # Create and return result
            return TaggingResult(
                tags=tags,
                confidence_scores=confidence_scores,
                model_used=model_used,
                raw_response=response_content
            )
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response: {e}")

    def _apply_filters(self, result: TaggingResult) -> TaggingResult:
        """Apply confidence and count filters to tagging result.
        
        Args:
            result: Original tagging result
            
        Returns:
            Filtered tagging result
        """
        # Filter by confidence threshold
        filtered_items = [
            (tag, score) for tag, score in result.confidence_scores.items()
            if score >= self.config.min_confidence
        ]
        
        # Sort by confidence score (descending)
        filtered_items.sort(key=lambda x: x[1], reverse=True)
        
        # Limit to max_tags
        filtered_items = filtered_items[:self.config.max_tags]
        
        # Extract filtered tags and scores
        filtered_tags = [item[0] for item in filtered_items]
        filtered_scores = {item[0]: item[1] for item in filtered_items}
        
        return TaggingResult(
            tags=filtered_tags,
            confidence_scores=filtered_scores,
            model_used=result.model_used,
            raw_response=result.raw_response
        )
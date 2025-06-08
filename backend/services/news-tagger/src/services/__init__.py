"""Services for the news tagger service."""

from .llm_service import LLMService, TaggingResult

__all__ = ["LLMService", "TaggingResult"]
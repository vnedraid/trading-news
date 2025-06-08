"""Configuration models for the news tagger service."""

from typing import List, Optional, Dict, Any


class LLMConfig:
    """Configuration for LLM API integration."""

    def __init__(
        self,
        api_key: str,
        model: str,
        provider: str = "openrouter",
        base_url: str = "https://openrouter.ai/api/v1",
        max_tokens: int = 150,
        temperature: float = 0.3,
        timeout: float = 30.0
    ):
        """Initialize LLM configuration.
        
        Args:
            api_key: API key for the LLM service
            model: Model name to use (e.g., "anthropic/claude-3-haiku")
            provider: LLM provider name
            base_url: Base URL for the API
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            timeout: Request timeout in seconds
        """
        self.provider = provider
        self.api_key = self._validate_api_key(api_key)
        self.model = self._validate_model(model)
        self.base_url = base_url
        self.max_tokens = self._validate_max_tokens(max_tokens)
        self.temperature = self._validate_temperature(temperature)
        self.timeout = timeout

    def _validate_api_key(self, api_key: str) -> str:
        """Validate API key."""
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")
        return api_key.strip()

    def _validate_model(self, model: str) -> str:
        """Validate model name."""
        if not model or not model.strip():
            raise ValueError("Model cannot be empty")
        return model.strip()

    def _validate_max_tokens(self, max_tokens: int) -> int:
        """Validate max_tokens value."""
        if max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        return max_tokens

    def _validate_temperature(self, temperature: float) -> float:
        """Validate temperature value."""
        if not (0 <= temperature <= 2):
            raise ValueError("Temperature must be between 0 and 2")
        return temperature

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        """Create from dictionary."""
        return cls(
            provider=data.get("provider", "openrouter"),
            api_key=data["api_key"],
            model=data["model"],
            base_url=data.get("base_url", "https://openrouter.ai/api/v1"),
            max_tokens=data.get("max_tokens", 150),
            temperature=data.get("temperature", 0.3),
            timeout=data.get("timeout", 30.0)
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"LLMConfig(provider='{self.provider}', model='{self.model}')"


class TaggerConfig:
    """Configuration for the news tagging service."""

    DEFAULT_CATEGORIES = [
        "finance",
        "trading",
        "markets",
        "economy",
        "politics",
        "technology",
        "business",
        "cryptocurrency",
        "stocks",
        "bonds",
        "commodities",
        "forex",
        "central-banking",
        "regulation",
        "earnings",
        "mergers-acquisitions",
        "ipo",
        "inflation",
        "gdp",
        "employment"
    ]

    def __init__(
        self,
        llm: LLMConfig,
        max_tags: int = 5,
        min_confidence: float = 0.5,
        categories: Optional[List[str]] = None
    ):
        """Initialize tagger configuration.
        
        Args:
            llm: LLM configuration
            max_tags: Maximum number of tags to generate
            min_confidence: Minimum confidence score for tags
            categories: List of allowed tag categories
        """
        self.llm = llm
        self.max_tags = self._validate_max_tags(max_tags)
        self.min_confidence = self._validate_min_confidence(min_confidence)
        self.categories = self._validate_categories(categories if categories is not None else self.DEFAULT_CATEGORIES)

    def _validate_max_tags(self, max_tags: int) -> int:
        """Validate max_tags value."""
        if max_tags <= 0:
            raise ValueError("Max tags must be positive")
        return max_tags

    def _validate_min_confidence(self, min_confidence: float) -> float:
        """Validate min_confidence value."""
        if not (0 <= min_confidence <= 1):
            raise ValueError("Min confidence must be between 0 and 1")
        return min_confidence

    def _validate_categories(self, categories: List[str]) -> List[str]:
        """Validate categories list."""
        if not categories:
            raise ValueError("Categories cannot be empty")
        return [cat.strip() for cat in categories if cat.strip()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "llm": self.llm.to_dict(),
            "max_tags": self.max_tags,
            "min_confidence": self.min_confidence,
            "categories": self.categories
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaggerConfig":
        """Create from dictionary."""
        llm_config = LLMConfig.from_dict(data["llm"])
        return cls(
            llm=llm_config,
            max_tags=data.get("max_tags", 5),
            min_confidence=data.get("min_confidence", 0.5),
            categories=data.get("categories")
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"TaggerConfig(max_tags={self.max_tags}, categories={len(self.categories)} items)"
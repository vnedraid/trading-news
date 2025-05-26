"""Custom exceptions for the trading bot backend."""

from typing import Any, Dict, Optional


class TradingBotException(Exception):
    """Base exception for all trading bot errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(TradingBotException):
    """Raised when there's a configuration error."""
    pass


class DatabaseError(TradingBotException):
    """Raised when there's a database-related error."""
    pass


class ExternalAPIError(TradingBotException):
    """Raised when there's an error with external API calls."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        self.api_name = api_name
        self.status_code = status_code
        self.response_data = response_data or {}
        
        details = kwargs.get("details", {})
        details.update({
            "api_name": api_name,
            "status_code": status_code,
            "response_data": response_data
        })
        
        super().__init__(message, kwargs.get("error_code"), details)


class DataProcessingError(TradingBotException):
    """Raised when there's an error processing data."""
    pass


class NewsCollectionError(TradingBotException):
    """Raised when there's an error collecting news data."""
    pass


class MarketDataError(TradingBotException):
    """Raised when there's an error with market data operations."""
    pass


class AIProcessingError(TradingBotException):
    """Raised when there's an error with AI/ML processing."""
    pass


class ChatError(TradingBotException):
    """Raised when there's an error with chat operations."""
    pass


class ValidationError(TradingBotException):
    """Raised when data validation fails."""
    pass


class RateLimitError(TradingBotException):
    """Raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        self.retry_after = retry_after
        
        details = kwargs.get("details", {})
        details["retry_after"] = retry_after
        
        super().__init__(message, kwargs.get("error_code"), details)


class AuthenticationError(TradingBotException):
    """Raised when there's an authentication error."""
    pass


class AuthorizationError(TradingBotException):
    """Raised when there's an authorization error."""
    pass


class NotFoundError(TradingBotException):
    """Raised when a requested resource is not found."""
    pass


class ConflictError(TradingBotException):
    """Raised when there's a conflict with the current state."""
    pass


class ServiceUnavailableError(TradingBotException):
    """Raised when a service is temporarily unavailable."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        retry_after: Optional[int] = None,
        **kwargs: Any
    ) -> None:
        self.service_name = service_name
        self.retry_after = retry_after
        
        details = kwargs.get("details", {})
        details.update({
            "service_name": service_name,
            "retry_after": retry_after
        })
        
        super().__init__(message, kwargs.get("error_code"), details)
"""Configuration management for the trading bot backend."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # PostgreSQL settings
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="trading_bot", description="PostgreSQL username")
    postgres_password: str = Field(description="PostgreSQL password")
    postgres_database: str = Field(default="trading_bot", description="PostgreSQL database name")
    
    # Elasticsearch settings
    elasticsearch_host: str = Field(default="localhost", description="Elasticsearch host")
    elasticsearch_port: int = Field(default=9200, description="Elasticsearch port")
    elasticsearch_username: Optional[str] = Field(default=None, description="Elasticsearch username")
    elasticsearch_password: Optional[str] = Field(default=None, description="Elasticsearch password")
    elasticsearch_use_ssl: bool = Field(default=False, description="Use SSL for Elasticsearch")
    
    # Redis settings
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"


class APISettings(BaseSettings):
    """External API configuration settings."""
    
    # OpenAI settings
    openai_api_key: str = Field(description="OpenAI API key")
    openai_model: str = Field(default="gpt-4", description="OpenAI model to use")
    openai_max_tokens: int = Field(default=1000, description="Maximum tokens for OpenAI responses")
    openai_temperature: float = Field(default=0.7, description="Temperature for OpenAI responses")
    
    # Alpha Vantage settings
    alpha_vantage_api_key: str = Field(description="Alpha Vantage API key")
    alpha_vantage_base_url: str = Field(default="https://www.alphavantage.co/query", description="Alpha Vantage base URL")
    
    # NewsAPI settings
    newsapi_key: Optional[str] = Field(default=None, description="NewsAPI key")
    newsapi_base_url: str = Field(default="https://newsapi.org/v2", description="NewsAPI base URL")
    
    # Yahoo Finance settings (no API key required)
    yahoo_finance_base_url: str = Field(default="https://query1.finance.yahoo.com/v8/finance/chart", description="Yahoo Finance base URL")
    
    # Twelve Data settings
    twelve_data_api_key: Optional[str] = Field(default=None, description="Twelve Data API key")
    twelve_data_base_url: str = Field(default="https://api.twelvedata.com", description="Twelve Data base URL")


class AppSettings(BaseSettings):
    """Application configuration settings."""
    
    # Application settings
    app_name: str = Field(default="Trading Bot Backend", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    
    # CORS settings
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    cors_methods: List[str] = Field(default=["*"], description="CORS allowed methods")
    cors_headers: List[str] = Field(default=["*"], description="CORS allowed headers")
    
    # Security settings
    secret_key: str = Field(description="Secret key for JWT and other security features")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration time in minutes")
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    # Background tasks
    celery_broker_url: Optional[str] = Field(default=None, description="Celery broker URL")
    celery_result_backend: Optional[str] = Field(default=None, description="Celery result backend URL")
    
    # Data collection intervals (in seconds)
    news_collection_interval: int = Field(default=300, description="News collection interval in seconds")
    market_data_interval: int = Field(default=60, description="Market data collection interval in seconds")
    cleanup_interval: int = Field(default=86400, description="Data cleanup interval in seconds")
    
    # Data retention (in days)
    news_retention_days: int = Field(default=30, description="News data retention in days")
    market_data_retention_days: int = Field(default=365, description="Market data retention in days")
    chat_history_retention_days: int = Field(default=90, description="Chat history retention in days")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json, text)")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_rotation: str = Field(default="1 day", description="Log rotation interval")
    log_retention: str = Field(default="30 days", description="Log retention period")


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    api: APISettings = Field(default_factory=APISettings)
    app: AppSettings = Field(default_factory=AppSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    class Config:
        env_nested_delimiter = "__"


# Global settings instance
settings = Settings()
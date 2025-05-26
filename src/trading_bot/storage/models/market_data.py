"""Market data models for PostgreSQL storage."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from ...core.database import Base


class Instrument(Base):
    """Financial instrument model."""
    
    __tablename__ = "instruments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    instrument_type = Column(String(20), nullable=False)  # stock, forex, crypto, commodity
    exchange = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(BigInteger, nullable=True)
    description = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)  # Using Integer instead of Boolean for better compatibility
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_instruments_type_exchange", "instrument_type", "exchange"),
        Index("idx_instruments_sector_industry", "sector", "industry"),
    )


class MarketQuote(Base):
    """Real-time and historical market quotes."""
    
    __tablename__ = "market_quotes"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(Numeric(20, 8), nullable=True)
    high_price = Column(Numeric(20, 8), nullable=True)
    low_price = Column(Numeric(20, 8), nullable=True)
    close_price = Column(Numeric(20, 8), nullable=False)
    volume = Column(BigInteger, nullable=True)
    adjusted_close = Column(Numeric(20, 8), nullable=True)
    dividend_amount = Column(Numeric(20, 8), nullable=True)
    split_coefficient = Column(Numeric(10, 4), nullable=True)
    data_source = Column(String(50), nullable=False)  # alpha_vantage, yahoo_finance, twelve_data
    quote_type = Column(String(20), nullable=False, default="daily")  # intraday, daily, weekly, monthly
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("symbol", "timestamp", "data_source", "quote_type", name="uq_market_quotes"),
        Index("idx_market_quotes_symbol_timestamp", "symbol", "timestamp"),
        Index("idx_market_quotes_timestamp", "timestamp"),
        Index("idx_market_quotes_source_type", "data_source", "quote_type"),
        # Partitioning by timestamp for better performance (would be set up in migration)
    )


class TechnicalIndicator(Base):
    """Technical indicators calculated from market data."""
    
    __tablename__ = "technical_indicators"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    indicator_name = Column(String(50), nullable=False)  # RSI, MACD, SMA, EMA, etc.
    indicator_value = Column(Numeric(20, 8), nullable=False)
    indicator_params = Column(JSONB, nullable=True)  # Parameters used for calculation
    timeframe = Column(String(20), nullable=False, default="daily")  # 1m, 5m, 15m, 1h, daily, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("symbol", "timestamp", "indicator_name", "timeframe", name="uq_technical_indicators"),
        Index("idx_technical_indicators_symbol_name", "symbol", "indicator_name"),
        Index("idx_technical_indicators_timestamp", "timestamp"),
        Index("idx_technical_indicators_name_timeframe", "indicator_name", "timeframe"),
    )


class MarketEvent(Base):
    """Significant market events and alerts."""
    
    __tablename__ = "market_events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # price_alert, volume_spike, technical_signal, etc.
    event_title = Column(String(255), nullable=False)
    event_description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    price_at_event = Column(Numeric(20, 8), nullable=True)
    volume_at_event = Column(BigInteger, nullable=True)
    event_data = Column(JSONB, nullable=True)  # Additional event-specific data
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_market_events_symbol_type", "symbol", "event_type"),
        Index("idx_market_events_timestamp", "timestamp"),
        Index("idx_market_events_severity", "severity"),
    )


class UserWatchlist(Base):
    """User watchlists for tracking specific instruments."""
    
    __tablename__ = "user_watchlists"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), nullable=False, index=True)  # Will be used when user auth is implemented
    watchlist_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    alert_price_above = Column(Numeric(20, 8), nullable=True)
    alert_price_below = Column(Numeric(20, 8), nullable=True)
    alert_volume_threshold = Column(BigInteger, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("user_id", "watchlist_name", "symbol", name="uq_user_watchlists"),
        Index("idx_user_watchlists_user_id", "user_id"),
        Index("idx_user_watchlists_symbol", "symbol"),
    )


class ChatSession(Base):
    """Chat sessions for tracking user conversations."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(String(100), primary_key=True)  # UUID
    user_id = Column(String(100), nullable=True, index=True)  # Optional user identification
    session_name = Column(String(255), nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    last_activity = Column(DateTime(timezone=True), nullable=False, index=True)
    session_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    __table_args__ = (
        Index("idx_chat_sessions_user_id", "user_id"),
        Index("idx_chat_sessions_last_activity", "last_activity"),
    )


class ChatMessage(Base):
    """Individual chat messages within sessions."""
    
    __tablename__ = "chat_messages"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    message_type = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    symbols_mentioned = Column(JSONB, nullable=True)  # Array of symbols mentioned in the message
    market_data_used = Column(JSONB, nullable=True)  # Market data that was used to generate response
    processing_time_ms = Column(Integer, nullable=True)
    ai_model_used = Column(String(50), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        Index("idx_chat_messages_session_id", "session_id"),
        Index("idx_chat_messages_timestamp", "timestamp"),
        Index("idx_chat_messages_type", "message_type"),
    )


class SystemConfig(Base):
    """System configuration and feature flags."""
    
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), nullable=False, unique=True, index=True)
    config_value = Column(Text, nullable=True)
    config_type = Column(String(20), nullable=False, default="string")  # string, integer, float, boolean, json
    description = Column(Text, nullable=True)
    is_sensitive = Column(Integer, nullable=False, default=0)  # For API keys, passwords, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
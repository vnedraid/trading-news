"""Database connection and session management."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings
from .exceptions import DatabaseError

# SQLAlchemy Base
Base = declarative_base()

# Global database instances
_async_engine: Optional[object] = None
_async_session_factory: Optional[async_sessionmaker] = None
_elasticsearch_client: Optional[AsyncElasticsearch] = None
_redis_client: Optional[Redis] = None


class DatabaseManager:
    """Database connection manager for PostgreSQL, Elasticsearch, and Redis."""
    
    def __init__(self) -> None:
        self._async_engine: Optional[object] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._elasticsearch_client: Optional[AsyncElasticsearch] = None
        self._redis_client: Optional[Redis] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all database connections."""
        if self._initialized:
            return
        
        try:
            await self._initialize_postgres()
            await self._initialize_elasticsearch()
            await self._initialize_redis()
            self._initialized = True
        except Exception as e:
            raise DatabaseError(f"Failed to initialize databases: {str(e)}")
    
    async def _initialize_postgres(self) -> None:
        """Initialize PostgreSQL connection."""
        try:
            # Create async engine
            self._async_engine = create_async_engine(
                settings.database.postgres_url,
                echo=settings.app.debug,
                poolclass=NullPool if settings.app.debug else None,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections every hour
            )
            
            # Create session factory
            self._async_session_factory = async_sessionmaker(
                bind=self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            
            # Test connection
            async with self._async_engine.begin() as conn:
                await conn.execute("SELECT 1")
                
        except Exception as e:
            raise DatabaseError(f"Failed to initialize PostgreSQL: {str(e)}")
    
    async def _initialize_elasticsearch(self) -> None:
        """Initialize Elasticsearch connection."""
        try:
            # Build Elasticsearch configuration
            es_config = {
                "hosts": [f"{settings.database.elasticsearch_host}:{settings.database.elasticsearch_port}"],
                "verify_certs": settings.database.elasticsearch_use_ssl,
                "ssl_show_warn": False,
            }
            
            # Add authentication if provided
            if settings.database.elasticsearch_username and settings.database.elasticsearch_password:
                es_config["basic_auth"] = (
                    settings.database.elasticsearch_username,
                    settings.database.elasticsearch_password
                )
            
            # Create client
            self._elasticsearch_client = AsyncElasticsearch(**es_config)
            
            # Test connection
            await self._elasticsearch_client.ping()
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize Elasticsearch: {str(e)}")
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            # Create Redis client
            self._redis_client = Redis.from_url(
                settings.database.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )
            
            # Test connection
            await self._redis_client.ping()
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize Redis: {str(e)}")
    
    async def close(self) -> None:
        """Close all database connections."""
        if self._async_engine:
            await self._async_engine.dispose()
        
        if self._elasticsearch_client:
            await self._elasticsearch_client.close()
        
        if self._redis_client:
            await self._redis_client.close()
        
        self._initialized = False
    
    @asynccontextmanager
    async def get_postgres_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get PostgreSQL session context manager."""
        if not self._async_session_factory:
            raise DatabaseError("PostgreSQL not initialized")
        
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @property
    def elasticsearch(self) -> AsyncElasticsearch:
        """Get Elasticsearch client."""
        if not self._elasticsearch_client:
            raise DatabaseError("Elasticsearch not initialized")
        return self._elasticsearch_client
    
    @property
    def redis(self) -> Redis:
        """Get Redis client."""
        if not self._redis_client:
            raise DatabaseError("Redis not initialized")
        return self._redis_client
    
    @property
    def postgres_engine(self) -> object:
        """Get PostgreSQL engine."""
        if not self._async_engine:
            raise DatabaseError("PostgreSQL not initialized")
        return self._async_engine


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for backward compatibility
async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """Get PostgreSQL session."""
    async with db_manager.get_postgres_session() as session:
        yield session


def get_elasticsearch() -> AsyncElasticsearch:
    """Get Elasticsearch client."""
    return db_manager.elasticsearch


def get_redis() -> Redis:
    """Get Redis client."""
    return db_manager.redis


async def init_databases() -> None:
    """Initialize all databases."""
    await db_manager.initialize()


async def close_databases() -> None:
    """Close all database connections."""
    await db_manager.close()


# Health check functions
async def check_postgres_health() -> bool:
    """Check PostgreSQL health."""
    try:
        async with get_postgres_session() as session:
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
    except Exception:
        return False


async def check_elasticsearch_health() -> bool:
    """Check Elasticsearch health."""
    try:
        es = get_elasticsearch()
        return await es.ping()
    except Exception:
        return False


async def check_redis_health() -> bool:
    """Check Redis health."""
    try:
        redis = get_redis()
        return await redis.ping()
    except Exception:
        return False


async def check_all_databases_health() -> dict[str, bool]:
    """Check health of all databases."""
    return {
        "postgres": await check_postgres_health(),
        "elasticsearch": await check_elasticsearch_health(),
        "redis": await check_redis_health(),
    }
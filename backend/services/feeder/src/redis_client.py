"""Redis client for duplicate detection and caching."""

import asyncio
import logging
from typing import Optional, Set, List
from datetime import timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.models.source_config import RedisConfig


logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client for duplicate detection and caching."""
    
    def __init__(self, config: RedisConfig):
        """Initialize Redis client with configuration."""
        self.config = config
        self._client: Optional[redis.Redis] = None
        self._connected = False
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, falling back to in-memory storage")
            self._memory_cache: Set[str] = set()
        
    async def connect(self) -> None:
        """Connect to Redis server."""
        if not REDIS_AVAILABLE:
            logger.info("Using in-memory cache instead of Redis")
            self._connected = True
            return
            
        try:
            self._client = redis.Redis(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password if self.config.password else None,
                decode_responses=True,
                socket_connect_timeout=self.config.connection_timeout_seconds,
                socket_timeout=self.config.operation_timeout_seconds,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self._client.ping()
            self._connected = True
            logger.info(f"Connected to Redis at {self.config.host}:{self.config.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.info("Falling back to in-memory cache")
            self._memory_cache = set()
            self._connected = True  # Still mark as connected for fallback mode
            
    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._client:
            await self._client.close()
            self._client = None
        self._connected = False
        logger.info("Disconnected from Redis")
        
    def is_connected(self) -> bool:
        """Check if connected to Redis or using fallback."""
        return self._connected
        
    async def is_duplicate(self, content_hash: str) -> bool:
        """Check if a content hash has been seen before."""
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
            
        try:
            if self._client:
                # Use Redis
                key = f"news:hash:{content_hash}"
                exists = await self._client.exists(key)
                return bool(exists)
            else:
                # Use in-memory fallback
                return content_hash in self._memory_cache
                
        except Exception as e:
            logger.error(f"Error checking duplicate for {content_hash}: {e}")
            # On error, assume not duplicate to avoid losing news
            return False
            
    async def mark_as_processed(self, content_hash: str, ttl_hours: int = 24) -> None:
        """Mark a content hash as processed with TTL."""
        if not self._connected:
            raise RuntimeError("Not connected to Redis")
            
        try:
            if self._client:
                # Use Redis with TTL
                key = f"news:hash:{content_hash}"
                await self._client.setex(key, timedelta(hours=ttl_hours), "1")
            else:
                # Use in-memory fallback
                self._memory_cache.add(content_hash)
                
                # Simple cleanup for memory cache
                if len(self._memory_cache) > 10000:
                    # Keep only recent 5000 items (simple FIFO)
                    self._memory_cache = set(list(self._memory_cache)[-5000:])
                    
        except Exception as e:
            logger.error(f"Error marking {content_hash} as processed: {e}")
            
    async def get_processed_count(self) -> int:
        """Get the number of processed items."""
        if not self._connected:
            return 0
            
        try:
            if self._client:
                # Count keys with news:hash: prefix
                keys = await self._client.keys("news:hash:*")
                return len(keys)
            else:
                # Return in-memory cache size
                return len(self._memory_cache)
                
        except Exception as e:
            logger.error(f"Error getting processed count: {e}")
            return 0
            
    async def cleanup_expired(self) -> int:
        """Cleanup expired entries (Redis handles this automatically with TTL)."""
        if not self._connected:
            return 0
            
        try:
            if self._client:
                # Redis handles TTL automatically, but we can scan for debugging
                keys = await self._client.keys("news:hash:*")
                return len(keys)
            else:
                # For in-memory, we already do cleanup in mark_as_processed
                return len(self._memory_cache)
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
            
    async def health_check(self) -> bool:
        """Check Redis health."""
        if not self._connected:
            return False
            
        try:
            if self._client:
                await self._client.ping()
                return True
            else:
                # In-memory fallback is always "healthy"
                return True
                
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False
            
    async def get_stats(self) -> dict:
        """Get Redis statistics."""
        stats = {
            "connected": self._connected,
            "using_redis": self._client is not None,
            "processed_count": await self.get_processed_count()
        }
        
        if self._client:
            try:
                info = await self._client.info()
                stats.update({
                    "redis_version": info.get("redis_version", "unknown"),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                })
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
                
        return stats


class DuplicateDetector:
    """High-level duplicate detection service."""
    
    def __init__(self, redis_config: RedisConfig):
        """Initialize duplicate detector with Redis config."""
        self.redis_client = RedisClient(redis_config)
        
    async def initialize(self) -> None:
        """Initialize the duplicate detector."""
        await self.redis_client.connect()
        
    async def cleanup(self) -> None:
        """Cleanup the duplicate detector."""
        await self.redis_client.disconnect()
        
    async def is_duplicate(self, content_hash: str) -> bool:
        """Check if content is duplicate."""
        return await self.redis_client.is_duplicate(content_hash)
        
    async def mark_processed(self, content_hash: str, ttl_hours: int = 24) -> None:
        """Mark content as processed."""
        await self.redis_client.mark_as_processed(content_hash, ttl_hours)
        
    async def get_stats(self) -> dict:
        """Get duplicate detection statistics."""
        return await self.redis_client.get_stats()
        
    def is_healthy(self) -> bool:
        """Check if duplicate detector is healthy."""
        return self.redis_client.is_connected()


# Global instance for easy access
_global_detector: Optional[DuplicateDetector] = None


async def get_duplicate_detector(redis_config: RedisConfig) -> DuplicateDetector:
    """Get or create global duplicate detector instance."""
    global _global_detector
    
    if _global_detector is None:
        _global_detector = DuplicateDetector(redis_config)
        await _global_detector.initialize()
        
    return _global_detector


async def cleanup_duplicate_detector() -> None:
    """Cleanup global duplicate detector instance."""
    global _global_detector
    
    if _global_detector:
        await _global_detector.cleanup()
        _global_detector = None
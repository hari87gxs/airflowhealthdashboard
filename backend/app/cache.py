"""
Caching Service
Provides in-memory caching with optional Redis backend.
"""

import json
from typing import Optional, Any
from datetime import datetime, timedelta
from loguru import logger
from app.config import settings


class CacheService:
    """Simple caching service with in-memory fallback."""
    
    def __init__(self):
        self.use_redis = False
        self.redis_client = None
        self.memory_cache: dict = {}
        self.cache_timestamps: dict = {}
        
        # Try to initialize Redis if URL is provided
        if settings.redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(
                    settings.redis_url,
                    decode_responses=True
                )
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis, using in-memory cache: {str(e)}")
                self.use_redis = False
        else:
            logger.info("No Redis URL provided, using in-memory cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            if self.use_redis:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Check in-memory cache
                if key in self.memory_cache:
                    timestamp = self.cache_timestamps.get(key)
                    if timestamp and datetime.utcnow() - timestamp < timedelta(seconds=settings.cache_ttl_seconds):
                        return self.memory_cache[key]
                    else:
                        # Expired
                        del self.memory_cache[key]
                        del self.cache_timestamps[key]
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache with optional TTL."""
        try:
            ttl = ttl or settings.cache_ttl_seconds
            
            if self.use_redis:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value, default=str)
                )
            else:
                # In-memory cache
                self.memory_cache[key] = value
                self.cache_timestamps[key] = datetime.utcnow()
                
                # Simple cleanup: remove old entries if cache grows too large
                if len(self.memory_cache) > 1000:
                    self._cleanup_memory_cache()
            
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        try:
            if self.use_redis:
                self.redis_client.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    del self.cache_timestamps[key]
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all cache entries."""
        try:
            if self.use_redis:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
                self.cache_timestamps.clear()
            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def _cleanup_memory_cache(self):
        """Remove expired entries from memory cache."""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp >= timedelta(seconds=settings.cache_ttl_seconds):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
            del self.cache_timestamps[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_status(self) -> str:
        """Get cache status for health checks."""
        if self.use_redis:
            try:
                self.redis_client.ping()
                return "redis_healthy"
            except:
                return "redis_error"
        else:
            return f"in_memory_{len(self.memory_cache)}_entries"


# Global cache instance
cache_service = CacheService()

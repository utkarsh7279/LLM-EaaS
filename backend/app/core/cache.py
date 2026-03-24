"""Redis caching layer for performance optimization."""

import json
import logging
from typing import Any, Optional

try:
    import redis.asyncio as redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis-based caching for experiment results and metrics."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", enabled: bool = True):
        self.redis_url = redis_url
        self.enabled = enabled and HAS_REDIS
        self.client: Optional[redis.Redis] = None

    async def connect(self):
        """Establish Redis connection."""
        if not self.enabled:
            logger.warning("Redis cache is disabled")
            return

        try:
            self.client = await redis.from_url(self.redis_url, decode_responses=True)
            await self.client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False

    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled or not self.client:
            return None

        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache read error for key {key}: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        if not self.enabled or not self.client:
            return False

        try:
            await self.client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache write error for key {key}: {e}")
            return False

    async def invalidate(self, key: str) -> bool:
        """Remove value from cache."""
        if not self.enabled or not self.client:
            return False

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache invalidation error for key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Remove all keys matching a pattern."""
        if not self.enabled or not self.client:
            return 0

        try:
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {e}")
            return 0


class CacheKeyBuilder:
    """Build consistent cache keys."""

    @staticmethod
    def experiment_results(experiment_id: str) -> str:
        """Key for experiment results."""
        return f"experiment:results:{experiment_id}"

    @staticmethod
    def experiment_metrics(experiment_id: str) -> str:
        """Key for experiment metrics."""
        return f"experiment:metrics:{experiment_id}"

    @staticmethod
    def comparison_results(experiment_id_1: str, experiment_id_2: str) -> str:
        """Key for comparison results."""
        exp_ids = sorted([experiment_id_1, experiment_id_2])
        return f"experiment:comparison:{exp_ids[0]}:{exp_ids[1]}"

    @staticmethod
    def experiment_pattern(experiment_id: str) -> str:
        """Pattern for all experiment-related keys."""
        return f"experiment:{experiment_id}:*"

    @staticmethod
    def export_cache(experiment_id: str, format_type: str) -> str:
        """Key for exported results."""
        return f"export:{experiment_id}:{format_type}"


class CachedMetricsService:
    """Service for cached metrics retrieval."""

    def __init__(self, cache: RedisCache):
        self.cache = cache

    async def get_metrics(self, experiment_id: str) -> Optional[dict]:
        """Get metrics from cache or None if not cached."""
        key = CacheKeyBuilder.experiment_metrics(experiment_id)
        return await self.cache.get(key)

    async def set_metrics(self, experiment_id: str, metrics: dict, ttl: int = 86400):
        """Cache metrics for 24 hours by default."""
        key = CacheKeyBuilder.experiment_metrics(experiment_id)
        await self.cache.set(key, metrics, ttl=ttl)

    async def invalidate_experiment(self, experiment_id: str):
        """Invalidate all cache for an experiment."""
        pattern = CacheKeyBuilder.experiment_pattern(experiment_id)
        await self.cache.invalidate_pattern(pattern)

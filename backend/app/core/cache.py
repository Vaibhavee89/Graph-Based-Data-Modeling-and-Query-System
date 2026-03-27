"""Simple in-memory cache for query results."""
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib
import json


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default 5 minutes)
        """
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.

        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create a deterministic string from args and kwargs
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                self.hits += 1
                return value
            else:
                # Expired, remove from cache
                del self._cache[key]

        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        expiry_seconds = ttl if ttl is not None else self.default_ttl
        expiry = datetime.now() + timedelta(seconds=expiry_seconds)
        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate * 100, 2),
        }

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if now >= expiry
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


# Global cache instance
_cache_instance: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """
    Get global cache instance.

    Returns:
        Cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleCache(default_ttl=300)  # 5 minutes
    return _cache_instance


def clear_cache() -> None:
    """Clear the global cache."""
    cache = get_cache()
    cache.clear()

"""LLM Cache decorator for semantic caching of tool results.

This module provides a decorator that attaches cache config to a function
and captures the cache key value during execution.

Usage:
    @tool
    @llmcache(cache_key_field="query_intent", ttl=3600, distance_threshold=0.2)
    async def get_recommendation_resources(...):
        ...
"""

from typing import Optional


def llmcache(cache_key_field: Optional[str] = None, ttl: Optional[int] = None, distance_threshold: Optional[float] = None, plugin_resource: Optional[str] = None):
    """LLM Cache decorator for semantic caching of tool results.

    Args:
        cache_key_field: Name of the argument used as cache key.
        ttl: Cache time-to-live in seconds.
        distance_threshold: Semantic similarity threshold.
        plugin_resource: Resource identifier included in the cached ToolMessage payload.
    """
    def decorator(cls):
        cls.metadata = {
            "is_cache_enabled": True,
            "cache_key_field": cache_key_field,
            "ttl": ttl,
            "distance_threshold": distance_threshold,
            "plugin_resource": plugin_resource or None,
        }
        return cls
    return decorator


__all__ = ["llmcache"]

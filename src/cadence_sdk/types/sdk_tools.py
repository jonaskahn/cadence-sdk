"""Framework-agnostic tool definitions for Cadence SDK.

This module provides the UvTool class and @uvtool decorator for defining
tools that can be used across different orchestration frameworks.
"""

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel

DEFAULT_CACHE_TTL_SECONDS = 3600
DEFAULT_SIMILARITY_THRESHOLD = 0.85
DESCRIPTION_PREVIEW_LENGTH = 50


@dataclass
class CacheConfig:
    """Cache configuration for a UvTool.

    Attributes:
        enabled: Whether caching is enabled for this tool
        ttl: Time-to-live in seconds for cached results (default 3600 = 1 hour)
        similarity_threshold: Similarity threshold (0.0-1.0) for semantic matching
            (default 0.85). Higher values require closer matches.
        cache_key_fields: Optional list of parameter names to use for cache key.
            If None, all parameters are used.
    """

    enabled: bool = True
    ttl: int = DEFAULT_CACHE_TTL_SECONDS
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    cache_key_fields: Optional[List[str]] = None


class UvTool:
    """Framework-agnostic tool wrapper.

    A UvTool wraps a callable function and provides metadata for
    tool discovery and invocation across different orchestration frameworks.

    Attributes:
        name: Tool name (used for invocation)
        description: Human-readable tool description
        func: The underlying callable function
        args_schema: Optional Pydantic model defining the tool's arguments
        cache: Optional cache configuration for semantic caching
        metadata: Additional metadata
        is_async: Whether the tool is async
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        args_schema: Optional[type[BaseModel]] = None,
        cache: Optional[CacheConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_async: Optional[bool] = None,
    ):
        """Initialize a UvTool.

        Args:
            name: Tool name
            description: Tool description
            func: The function to wrap
            args_schema: Optional Pydantic model for args validation
            cache: Optional cache configuration
            metadata: Optional metadata dictionary
            is_async: Whether func is async (auto-detected if None)
        """
        self.name = name
        self.description = description
        self.func = func
        self.args_schema = args_schema
        self.cache = cache
        self.metadata = metadata or {}
        self.is_async = self._determine_async_nature(func, is_async)

    @staticmethod
    def _determine_async_nature(func: Callable, is_async: Optional[bool]) -> bool:
        """Determine if function is async.

        Args:
            func: Function to check
            is_async: Explicitly specified async flag (None for auto-detect)

        Returns:
            True if function is async
        """
        if is_async is not None:
            return is_async
        return asyncio.iscoroutinefunction(func)

    def __call__(self, *args, **kwargs) -> Any:
        """Synchronous invocation.

        Raises:
            RuntimeError: If tool is async (use ainvoke instead)
        """
        if self.is_async:
            raise RuntimeError(
                f"Tool '{self.name}' is async. Use ainvoke() instead of direct call."
            )
        return self.func(*args, **kwargs)

    async def ainvoke(self, *args, **kwargs) -> Any:
        """Async invocation.

        For sync tools, runs in executor. For async tools, awaits directly.

        Returns:
            Result from tool execution
        """
        if self.is_async:
            return await self.func(*args, **kwargs)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self.func(*args, **kwargs))

    def invoke(self, *args, **kwargs) -> Any:
        """Sync invocation alias.

        Returns:
            Result from tool execution
        """
        return self(*args, **kwargs)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"UvTool(name='{self.name}', "
            f"description='{self.description[:DESCRIPTION_PREVIEW_LENGTH]}...', "
            f"is_async={self.is_async})"
        )


def uvtool(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    args_schema: Optional[type[BaseModel]] = None,
    cache: Optional[Union[CacheConfig, bool, dict]] = None,
    **metadata,
) -> Union[Callable, UvTool]:
    """Decorator to convert a function into a UvTool.

    Can be used with or without parentheses:
        @uvtool
        def my_tool(query: str) -> str:
            '''Search for information.'''
            return search(query)

        @uvtool(name="custom_name", description="Custom description")
        async def async_tool(param: int) -> dict:
            result = await some_async_operation(param)
            return result

        @uvtool(cache=True)  # Enable caching with defaults
        def cached_tool(query: str) -> str:
            '''Expensive operation.'''
            return expensive_search(query)

        @uvtool(cache={"ttl": 7200, "similarity_threshold": 0.9})
        def custom_cache_tool(query: str) -> str:
            '''Custom cache settings.'''
            return search(query)

        @uvtool(cache=CacheConfig(ttl=3600, cache_key_fields=["query"]))
        def selective_cache(query: str, limit: int = 10) -> str:
            '''Only cache by query, ignore limit.'''
            return search(query, limit)

    Args:
        func: Function to decorate (when used without parentheses)
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        args_schema: Optional Pydantic model for argument validation
        cache: Cache configuration (True/False, dict, or CacheConfig instance)
        **metadata: Additional metadata to store in tool.metadata

    Returns:
        UvTool instance (when used without parentheses) or
        decorator function (when used with parentheses)
    """

    def _create_tool_from_function(fn: Callable) -> UvTool:
        """Create UvTool from function."""
        tool_name = name if name is not None else fn.__name__
        tool_description = _extract_description(fn, tool_name, description)
        is_async = asyncio.iscoroutinefunction(fn)
        cache_config = _build_cache_config(fn, cache)
        func_metadata = _merge_metadata(fn, metadata)

        tool = UvTool(
            name=tool_name,
            description=tool_description,
            func=fn,
            args_schema=args_schema,
            cache=cache_config,
            metadata=func_metadata,
            is_async=is_async,
        )

        _preserve_function_signature(tool, fn)
        return tool

    if func is not None:
        return _create_tool_from_function(func)
    else:
        return _create_tool_from_function


def _extract_description(
    fn: Callable, tool_name: str, explicit_description: Optional[str]
) -> str:
    """Extract tool description from function docstring or explicit parameter.

    Args:
        fn: Function to extract description from
        tool_name: Name of the tool (used as fallback)
        explicit_description: Explicitly provided description (takes precedence)

    Returns:
        Tool description string
    """
    if explicit_description is not None:
        return explicit_description

    doc = inspect.getdoc(fn)
    if doc:
        return doc.split("\n")[0].strip()

    return f"Tool: {tool_name}"


def _build_cache_config(
    fn: Callable, cache_param: Optional[Union[CacheConfig, bool, dict]]
) -> Optional[CacheConfig]:
    """Build cache configuration from function metadata and explicit parameter.

    Args:
        fn: Function that may have legacy cache metadata
        cache_param: Explicit cache parameter from decorator

    Returns:
        CacheConfig instance or None
    """
    cache_config = _extract_legacy_cache_config(fn)

    if cache_param is not None:
        cache_config = _parse_cache_parameter(cache_param)

    return cache_config


def _extract_legacy_cache_config(fn: Callable) -> Optional[CacheConfig]:
    """Extract cache config from legacy @llmcache decorator metadata.

    Args:
        fn: Function to check for legacy metadata

    Returns:
        CacheConfig if legacy metadata exists, None otherwise
    """
    if not hasattr(fn, "_cadence_metadata"):
        return None

    legacy_cache = fn._cadence_metadata
    if not legacy_cache.get("cache_enabled"):
        return None

    return CacheConfig(
        enabled=True,
        ttl=legacy_cache.get("cache_ttl", DEFAULT_CACHE_TTL_SECONDS),
        similarity_threshold=legacy_cache.get(
            "cache_similarity_threshold", DEFAULT_SIMILARITY_THRESHOLD
        ),
        cache_key_fields=legacy_cache.get("cache_key_fields"),
    )


def _parse_cache_parameter(
    cache_param: Union[CacheConfig, bool, dict],
) -> Optional[CacheConfig]:
    """Parse cache parameter into CacheConfig.

    Args:
        cache_param: Cache parameter (CacheConfig, bool, or dict)

    Returns:
        CacheConfig instance or None
    """
    if isinstance(cache_param, CacheConfig):
        return cache_param
    elif isinstance(cache_param, bool):
        return CacheConfig(enabled=cache_param) if cache_param else None
    elif isinstance(cache_param, dict):
        return CacheConfig(**cache_param)
    return None


def _merge_metadata(fn: Callable, additional_metadata: dict) -> Dict[str, Any]:
    """Merge function metadata with additional metadata.

    Args:
        fn: Function that may have existing metadata
        additional_metadata: Additional metadata to merge

    Returns:
        Merged metadata dictionary
    """
    func_metadata = dict(additional_metadata)

    if not hasattr(fn, "_cadence_metadata"):
        return func_metadata

    non_cache_metadata = {
        k: v for k, v in fn._cadence_metadata.items() if not k.startswith("cache_")
    }
    func_metadata.update(non_cache_metadata)

    return func_metadata


def _preserve_function_signature(tool: UvTool, fn: Callable) -> None:
    """Preserve original function signature on tool for introspection.

    Args:
        tool: UvTool instance to modify
        fn: Original function
    """
    tool.__signature__ = inspect.signature(fn)
    tool.__doc__ = fn.__doc__
    tool.__name__ = fn.__name__
    tool.__module__ = fn.__module__


def create_tool(
    name: str,
    description: str,
    func: Callable,
    args_schema: Optional[type[BaseModel]] = None,
    cache: Optional[Union[CacheConfig, bool, dict]] = None,
    **metadata,
) -> UvTool:
    """Programmatically create a UvTool without using decorator syntax.

    Args:
        name: Tool name
        description: Tool description
        func: Function to wrap
        args_schema: Optional Pydantic model for args
        cache: Cache configuration (True/False, dict, or CacheConfig instance)
        **metadata: Additional metadata

    Returns:
        UvTool instance
    """
    cache_config = _parse_cache_parameter(cache) if cache is not None else None

    return UvTool(
        name=name,
        description=description,
        func=func,
        args_schema=args_schema,
        cache=cache_config,
        metadata=metadata,
    )

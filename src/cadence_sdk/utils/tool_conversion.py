"""Tool conversion utilities for Cadence SDK.

This module provides utilities for converting Cadence tools to LangChain tools
with proper handling of async functions for structured output compatibility.
"""

import inspect
from typing import Any, Dict, List, Optional, Union

from langchain_core.tools import Tool

from ..base.loggable import Loggable


def convert_to_langchain_tool(cadence_tool: Any) -> Tool:
    """Convert a Cadence GenericTool to a LangChain Tool with proper async handling.

    Args:
        cadence_tool: The tool object from cadence_sdk (could be a function or Tool object)

    Returns:
        Tool: A LangChain Tool object compatible with structured output
    """
    target_function = _extract_target_function(cadence_tool)

    tool_name = _extract_tool_name(cadence_tool, target_function)
    tool_description = _extract_tool_description(cadence_tool, target_function)
    tool_args_schema = _extract_tool_args_schema(cadence_tool)
    tool_metadata = _extract_tool_metadata(cadence_tool)

    if _is_async_function(target_function):
        return _create_async_tool(tool_name, tool_description, target_function, tool_args_schema, tool_metadata)
    else:
        return _create_sync_tool(tool_name, tool_description, target_function, tool_args_schema, tool_metadata)


def _extract_target_function(cadence_tool: Any) -> Any:
    """Extract the actual function to use from a cadence tool."""
    # Handle different tool structures (sync vs async)
    coroutine_func = getattr(cadence_tool, "coroutine", None)
    sync_func = getattr(cadence_tool, "func", None)

    if coroutine_func is not None:
        return coroutine_func
    elif sync_func is not None:
        return sync_func
    else:
        return cadence_tool


def _extract_tool_name(cadence_tool: Any, target_function: Any) -> str:
    """Extract tool name from cadence tool or function."""
    return getattr(cadence_tool, "name", target_function.__name__)


def _extract_tool_description(cadence_tool: Any, target_function: Any) -> str:
    """Extract tool description from cadence tool or function."""
    return getattr(cadence_tool, "description", target_function.__doc__ or "")


def _extract_tool_args_schema(cadence_tool: Any) -> Any:
    """Extract tool args schema from cadence tool."""
    return getattr(cadence_tool, "args_schema", None)


def _extract_tool_metadata(cadence_tool: Any) -> Dict[str, Any]:
    """Extract tool metadata from cadence tool."""
    return getattr(cadence_tool, "metadata", {})


def _is_async_function(target_function: Any) -> bool:
    """Check if the target function is async."""
    return inspect.iscoroutinefunction(target_function)


def _create_async_tool(
    tool_name: str, tool_description: str, async_function: Any, args_schema: Any, metadata: Dict[str, Any]
) -> Tool:
    """Create a LangChain tool for async functions."""
    sync_wrapper = _create_sync_wrapper(async_function, tool_name, tool_description)

    return Tool(
        name=tool_name,
        description=tool_description,
        func=sync_wrapper,
        args_schema=args_schema,
        **metadata if metadata else {},
    )


def _create_sync_tool(
    tool_name: str, tool_description: str, sync_function: Any, args_schema: Any, metadata: Dict[str, Any]
) -> Tool:
    """Create a LangChain tool for sync functions."""
    return Tool(
        name=tool_name,
        description=tool_description,
        func=sync_function,
        args_schema=args_schema,
        **metadata if metadata else {},
    )


def _create_sync_wrapper(async_function: Any, tool_name: str, tool_description: str) -> Any:
    """Create a synchronous wrapper for an async function."""

    def sync_wrapper(*args, **kwargs):
        """Synchronous wrapper that returns a coroutine for async execution."""
        return async_function(*args, **kwargs)

    sync_wrapper.__name__ = tool_name
    sync_wrapper.__doc__ = tool_description
    sync_wrapper._async_func = async_function
    return sync_wrapper


def convert_tools_to_langchain_tools(tools: List[Any]) -> List[Tool]:
    """Convert a list of Cadence tools to LangChain tools.

    Args:
        tools: List of cadence_sdk tool objects or functions

    Returns:
        List[Tool]: List of LangChain Tool objects

    Raises:
        ValueError: If any tool conversion fails
    """
    converted_tools = []

    for tool_index, cadence_tool in enumerate(tools):
        try:
            langchain_tool = convert_to_langchain_tool(cadence_tool)
            converted_tools.append(langchain_tool)
        except Exception as e:
            raise ValueError(f"Failed to convert tool at index {tool_index}: {e}") from e

    return converted_tools


class ToolConversionManager(Loggable):
    """Manager for tool conversion operations with caching and error handling."""

    def __init__(self):
        super().__init__()
        self._conversion_cache: Dict[str, Tool] = {}

    def convert_tools_batch(self, tools: List[Any], use_cache: bool = True) -> List[Tool]:
        """Convert multiple tools with optional caching.

        Args:
            tools: List of tools to convert
            use_cache: Whether to use conversion cache

        Returns:
            List[Tool]: Converted LangChain tools
        """
        converted_tools = []

        for cadence_tool in tools:
            cache_key = self._generate_cache_key(cadence_tool)

            if use_cache and cache_key in self._conversion_cache:
                converted_tools.append(self._conversion_cache[cache_key])
                continue

            try:
                converted_tool = convert_to_langchain_tool(cadence_tool)
                if use_cache:
                    self._conversion_cache[cache_key] = converted_tool
                converted_tools.append(converted_tool)
            except Exception as e:
                self.logger.error(f"Failed to convert tool {cache_key}: {e}")
                raise

        return converted_tools

    def _generate_cache_key(self, cadence_tool: Any) -> str:
        """Generate a unique cache key for a tool based on its identity."""
        try:
            tool_name = getattr(cadence_tool, "name", None) or getattr(cadence_tool, "__name__", "unknown")
            return f"{id(cadence_tool)}_{tool_name}"
        except Exception:
            return f"{id(cadence_tool)}_unknown"

    def clear_cache(self) -> None:
        """Clear the conversion cache."""
        self._conversion_cache.clear()
        self.logger.debug("Tool conversion cache cleared")

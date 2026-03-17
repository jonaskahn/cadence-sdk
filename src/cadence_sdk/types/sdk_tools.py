"""Framework-agnostic tool definitions for Cadence SDK.

This module provides the UvTool class and @uvtool decorator for defining
tools that can be used across different orchestration frameworks.
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, Optional, Union

from pydantic import BaseModel
from typing_extensions import TypedDict

StreamFilter = Optional[Callable[[Any], Any]]

DESCRIPTION_PREVIEW_LENGTH = 50


class ToolRecord(TypedDict, total=False):
    """Internal executor record for a single tool invocation result.

    Never constructed by tool authors — built entirely by the executor node
    using the tool call metadata and tool_to_plugin_map.

    stream_tool: when True the executor also populates stream_data and the
        streaming wrapper emits a TOOL event to the client before the synthesizer.
    stream_data: the pre-filtered (client-safe) copy of data; only set when
        stream_tool=True. The original data field is always the unfiltered value
        used internally by the validator and synthesizer.
    """

    tool_name: str
    plugin_id: str
    data: Any
    required_validate: bool
    stream_tool: bool
    stream_data: Any


class UvTool:
    """Framework-agnostic tool wrapper.

    A UvTool wraps a callable function and provides metadata for
    tool discovery and invocation across different orchestration frameworks.

    Attributes:
        name: Tool name (used for invocation)
        description: Human-readable tool description
        func: The underlying callable function
        args_schema: Optional Pydantic model defining the tool's arguments
        metadata: Additional metadata
        required_validate: Whether tool output should be validated by the LLM
        stream_tool: When True the orchestrator streams the tool result to the
            client before the synthesizer runs. stream_filter is applied first
            so only client-safe data is transmitted.
        stream_filter: Optional sync or async callable ``(Any) -> Any`` applied
            to the raw tool result before streaming to the client. Does not
            affect the data that flows through the internal pipeline.
        is_async: Whether the tool is async
    """

    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        args_schema: Optional[type[BaseModel]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        required_validate: bool = False,
        stream_tool: bool = False,
        stream_filter: StreamFilter = None,
    ):
        self.name = name
        self.description = description
        self.func = func
        self.args_schema = args_schema
        self.metadata = metadata or {}
        self.required_validate = required_validate
        self.stream_tool = stream_tool
        self.stream_filter = stream_filter
        self.is_async = asyncio.iscoroutinefunction(func)

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
        """
        if self.is_async:
            return await self.func(*args, **kwargs)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: self.func(*args, **kwargs))

    def invoke(self, *args, **kwargs) -> Any:
        """Sync invocation alias."""
        return self(*args, **kwargs)

    def __repr__(self) -> str:
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
    stream: bool = False,
    stream_filter: StreamFilter = None,
    validate: bool = False,
    **metadata,
) -> Union[Callable, UvTool]:
    """Decorator to convert a function into a UvTool.

    Can be used with or without parentheses:
        @uvtool
        def my_tool(query: str) -> str:
            '''Search for information.'''
            return search(query)

        @uvtool(name="custom_name")
        async def async_tool(param: int) -> dict:
            return await some_async_operation(param)

        @uvtool(stream=True, stream_filter=lambda r: {k: v for k, v in r.items() if k != "secret"})
        async def streaming_tool(query: str) -> dict:
            '''Tool that streams its result to the client.'''
            return await fetch_data(query)

    Args:
        func: Function to decorate (when used without parentheses)
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        args_schema: Optional Pydantic model for argument validation
        stream: When True, the orchestrator streams the tool result to the client
            before the synthesizer runs. Use stream_filter to restrict which fields
            are exposed.
        stream_filter: Optional sync or async callable ``(Any) -> Any`` applied to
            the raw result before it is streamed to the client. The unfiltered result
            still flows through the internal pipeline (validator → synthesizer).
        validate: Whether the tool's output requires LLM validation. When True,
            the executor sets required_validate=True on the ToolRecord so the
            validator node knows to inspect this result against user intent.
        **metadata: Additional metadata to store in tool.metadata

    Returns:
        UvTool instance (when used without parentheses) or
        decorator function (when used with parentheses)
    """

    def _create_tool_from_function(func: Callable) -> UvTool:
        tool_name = name if name is not None else func.__name__
        tool_description = _extract_description(func, tool_name, description)
        tool = UvTool(
            name=tool_name,
            description=tool_description,
            func=func,
            args_schema=args_schema,
            metadata=dict(metadata),
            required_validate=validate,
            stream_tool=stream,
            stream_filter=stream_filter,
        )
        _preserve_function_signature(tool, func)
        return tool

    if func is not None:
        return _create_tool_from_function(func)
    return _create_tool_from_function


def _extract_description(
    func: Callable, tool_name: str, explicit_description: Optional[str]
) -> str:
    if explicit_description is not None:
        return explicit_description
    docstring = inspect.getdoc(func)
    if docstring:
        return docstring.split("\n")[0].strip()
    return f"Tool: {tool_name}"


def _preserve_function_signature(tool: UvTool, func: Callable) -> None:
    tool.__signature__ = inspect.signature(func)
    tool.__doc__ = func.__doc__
    tool.__name__ = func.__name__
    tool.__module__ = func.__module__

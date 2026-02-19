"""Tests for UvTool and uvtool decorator."""

import asyncio

import pytest
from cadence_sdk import CacheConfig, UvTool, uvtool


class TestCacheConfig:
    """Tests for CacheConfig dataclass."""

    def test_default_values(self):
        """CacheConfig has sensible defaults."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.ttl == 3600
        assert config.similarity_threshold == 0.85
        assert config.cache_key_fields is None

    def test_custom_values(self):
        """CacheConfig accepts custom values."""
        config = CacheConfig(
            enabled=False,
            ttl=7200,
            similarity_threshold=0.9,
            cache_key_fields=["query"],
        )
        assert config.enabled is False
        assert config.ttl == 7200
        assert config.similarity_threshold == 0.9
        assert config.cache_key_fields == ["query"]


class TestUvtoolDecorator:
    """Tests for @uvtool decorator."""

    def test_decorator_without_parentheses_creates_tool(self):
        """@uvtool without parentheses converts function to UvTool."""

        @uvtool
        def my_tool(x: str) -> str:
            """Echo input."""
            return x

        assert isinstance(my_tool, UvTool)
        assert my_tool.name == "my_tool"
        assert "Echo" in my_tool.description or "echo" in my_tool.description.lower()

    def test_decorator_with_parentheses_creates_tool(self):
        """@uvtool() with parentheses converts function to UvTool."""

        @uvtool()
        def other_tool(y: int) -> int:
            """Double the input."""
            return y * 2

        assert isinstance(other_tool, UvTool)
        assert other_tool.name == "other_tool"

    def test_decorator_with_name_override(self):
        """@uvtool(name=...) overrides tool name."""

        @uvtool(name="custom_name")
        def fn() -> str:
            """A function."""
            return "ok"

        assert fn.name == "custom_name"

    def test_decorator_with_description_override(self):
        """@uvtool(description=...) overrides description."""

        @uvtool(description="Custom description")
        def fn() -> str:
            return "ok"

        assert fn.description == "Custom description"

    def test_decorator_with_cache_true(self):
        """@uvtool(cache=True) enables caching."""

        @uvtool(cache=True)
        def cached_fn(q: str) -> str:
            return q

        assert cached_fn.cache is not None
        assert cached_fn.cache.enabled is True

    def test_decorator_with_cache_config(self):
        """@uvtool(cache=CacheConfig(...)) uses custom cache config."""

        @uvtool(cache=CacheConfig(ttl=100, similarity_threshold=0.95))
        def fn(q: str) -> str:
            return q

        assert fn.cache.ttl == 100
        assert fn.cache.similarity_threshold == 0.95


class TestUvToolInvocation:
    """Tests for UvTool invocation methods."""

    def test_sync_tool_invoke_returns_result(self):
        """Sync tool invoke returns function result."""

        @uvtool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        assert add.invoke(2, 3) == 5
        assert add(2, 3) == 5

    def test_async_tool_ainvoke_returns_result(self):
        """Async tool ainvoke returns awaited result."""

        @uvtool
        async def async_echo(x: str) -> str:
            """Async echo."""
            return x

        result = asyncio.run(async_echo.ainvoke("hello"))
        assert result == "hello"

    def test_sync_tool_ainvoke_runs_in_executor(self):
        """Sync tool ainvoke runs in executor for async compatibility."""

        @uvtool
        def sync_multiply(a: int, b: int) -> int:
            """Multiply."""
            return a * b

        result = asyncio.run(sync_multiply.ainvoke(4, 5))
        assert result == 20

    def test_async_tool_direct_call_raises_runtime_error(self):
        """Calling async tool directly raises RuntimeError."""

        @uvtool
        async def async_fn() -> str:
            return "ok"

        with pytest.raises(RuntimeError, match="Use ainvoke"):
            async_fn()


class TestUvToolAttributes:
    """Tests for UvTool attributes."""

    def test_preserves_function_signature(self):
        """UvTool preserves original function signature."""

        @uvtool
        def sig_test(a: int, b: str = "default") -> str:
            """Test."""
            return f"{a}{b}"

        assert hasattr(sig_test, "__signature__")
        assert sig_test.__name__ == "sig_test"

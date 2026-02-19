"""Tests for SDK message types."""

from cadence_sdk import (
    ToolCall,
    UvAIMessage,
    UvHumanMessage,
    UvSystemMessage,
    UvToolMessage,
)


class TestUvHumanMessage:
    """Tests for UvHumanMessage."""

    def test_creates_message_with_content(self):
        """UvHumanMessage accepts content and sets role to human."""
        msg = UvHumanMessage(content="Hello")
        assert msg.role == "human"
        assert msg.content == "Hello"
        assert msg.message_id is not None

    def test_accepts_optional_metadata_and_message_id(self):
        """UvHumanMessage accepts optional metadata and message_id."""
        msg = UvHumanMessage(
            content="Hi",
            metadata={"user_id": "123"},
            message_id="custom-id",
        )
        assert msg.metadata == {"user_id": "123"}
        assert msg.message_id == "custom-id"

    def test_to_dict_and_from_dict_roundtrip(self):
        """to_dict and from_dict preserve message data."""
        msg = UvHumanMessage(content="Roundtrip test")
        data = msg.to_dict()
        restored = UvHumanMessage.from_dict(data)
        assert restored.content == msg.content
        assert restored.role == msg.role


class TestUvAIMessage:
    """Tests for UvAIMessage."""

    def test_creates_message_with_content(self):
        """UvAIMessage accepts content and sets role to ai."""
        msg = UvAIMessage(content="I can help")
        assert msg.role == "ai"
        assert msg.content == "I can help"
        assert msg.tool_calls == []

    def test_accepts_tool_calls_as_objects(self):
        """UvAIMessage accepts ToolCall objects."""
        tc = ToolCall(name="search", args={"query": "test"})
        msg = UvAIMessage(content="", tool_calls=[tc])
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "search"
        assert msg.tool_calls[0].args == {"query": "test"}

    def test_accepts_tool_calls_as_dicts(self):
        """UvAIMessage normalizes tool call dicts to ToolCall objects."""
        msg = UvAIMessage(
            content="",
            tool_calls=[{"name": "fetch", "args": {"url": "https://example.com"}}],
        )
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "fetch"
        assert isinstance(msg.tool_calls[0], ToolCall)


class TestUvSystemMessage:
    """Tests for UvSystemMessage."""

    def test_creates_message_with_content(self):
        """UvSystemMessage accepts content and sets role to system."""
        msg = UvSystemMessage(content="You are helpful")
        assert msg.role == "system"
        assert msg.content == "You are helpful"


class TestUvToolMessage:
    """Tests for UvToolMessage."""

    def test_creates_message_with_required_fields(self):
        """UvToolMessage requires content, tool_call_id, tool_name."""
        msg = UvToolMessage(
            content="Result data",
            tool_call_id="call_123",
            tool_name="search",
        )
        assert msg.role == "tool"
        assert msg.content == "Result data"
        assert msg.tool_call_id == "call_123"
        assert msg.tool_name == "search"

    def test_accepts_string_content(self):
        """UvToolMessage accepts string content."""
        msg = UvToolMessage(
            content='{"result": "data"}',
            tool_call_id="call_1",
            tool_name="fetch",
        )
        assert msg.content == '{"result": "data"}'


class TestToolCall:
    """Tests for ToolCall model."""

    def test_creates_tool_call_with_required_fields(self):
        """ToolCall requires name and args."""
        tc = ToolCall(name="my_tool", args={"x": 1})
        assert tc.name == "my_tool"
        assert tc.args == {"x": 1}
        assert tc.id is not None

    def test_accepts_custom_id(self):
        """ToolCall accepts optional id."""
        tc = ToolCall(id="custom-id", name="tool", args={})
        assert tc.id == "custom-id"


class TestUvMessageBase:
    """Tests for UvMessage base class."""

    def test_to_dict_returns_serializable_dict(self):
        """to_dict returns dict suitable for JSON serialization."""
        msg = UvHumanMessage(content="Test")
        data = msg.to_dict()
        assert isinstance(data, dict)
        assert "role" in data
        assert "content" in data
        assert "message_id" in data

"""Framework-agnostic message types for Cadence SDK.

These message types provide a unified interface for agent communication
across different orchestration frameworks (LangGraph, OpenAI Agents, Google ADK).
"""

from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class UvMessage(BaseModel):
    """Base class for all Cadence SDK messages.

    Attributes:
        role: The role of the message sender (human, ai, system, tool)
        content: The message content (text or structured data)
        metadata: Optional metadata for extensibility
        message_id: Unique identifier for the message
    """

    role: str
    content: Union[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    message_id: str = Field(default_factory=lambda: str(uuid4()))

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "role": "human",
                    "content": "Hello, how can you help me?",
                    "metadata": {},
                    "message_id": "123e4567-e89b-12d3-a456-426614174000",
                }
            ]
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization.

        Returns:
            Dictionary representation of message
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UvMessage":
        """Create message from dictionary.

        Args:
            data: Dictionary containing message data

        Returns:
            UvMessage instance
        """
        return cls(**data)


class UvHumanMessage(UvMessage):
    """Message from a human user.

    Attributes:
        role: Always "human"
        content: The user's message text
        metadata: Optional metadata (e.g., user_id, timestamp)
        message_id: Unique identifier
    """

    role: str = Field(default="human", frozen=True)

    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ):
        """Initialize human message.

        Args:
            content: The message content
            metadata: Optional metadata
            message_id: Optional message ID (auto-generated if not provided)
        """
        init_data = {
            "role": "human",
            "content": content,
            "metadata": metadata or {},
        }
        if message_id:
            init_data["message_id"] = message_id
        super().__init__(**init_data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UvHumanMessage":
        """Create message from dictionary.

        Args:
            data: Dictionary containing message data

        Returns:
            UvHumanMessage instance
        """
        clean_data = cls._exclude_auto_fields(data, "role")
        return cls(**clean_data)

    @staticmethod
    def _exclude_auto_fields(data: Dict[str, Any], *fields: str) -> Dict[str, Any]:
        """Exclude fields that are automatically set by __init__.

        Args:
            data: Source dictionary
            *fields: Field names to exclude

        Returns:
            Filtered dictionary
        """
        return {k: v for k, v in data.items() if k not in fields}


class ToolCall(BaseModel):
    """Represents a tool invocation request from an AI.

    Attributes:
        id: Unique identifier for this tool call
        name: Name of the tool to invoke
        args: Arguments to pass to the tool
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    args: Dict[str, Any]

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "examples": [
                {
                    "id": "call_abc123",
                    "name": "search_tool",
                    "args": {"query": "Python tutorials"},
                }
            ]
        }


class UvAIMessage(UvMessage):
    """Message from an AI agent.

    Attributes:
        role: Always "ai"
        content: The AI's response text
        tool_calls: Optional list of tool invocations requested by the AI
        metadata: Optional metadata (e.g., model_name, tokens_used)
        message_id: Unique identifier
    """

    role: str = Field(default="ai", frozen=True)
    tool_calls: List[ToolCall] = Field(default_factory=list)

    def __init__(
        self,
        content: str = "",
        tool_calls: Optional[List[Union[ToolCall, Dict[str, Any]]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ):
        """Initialize AI message.

        Args:
            content: The message content (may be empty if only tool calls)
            tool_calls: Optional list of tool calls
            metadata: Optional metadata
            message_id: Optional message ID
        """
        processed_tool_calls = self._normalize_tool_calls(tool_calls)

        init_data = {
            "role": "ai",
            "content": content,
            "tool_calls": processed_tool_calls,
            "metadata": metadata or {},
        }
        if message_id:
            init_data["message_id"] = message_id
        super().__init__(**init_data)

    @staticmethod
    def _normalize_tool_calls(
        tool_calls: Optional[List[Union[ToolCall, Dict[str, Any]]]],
    ) -> List[ToolCall]:
        """Convert tool call dicts to ToolCall objects."""
        if not tool_calls:
            return []

        return [ToolCall(**tc) if isinstance(tc, dict) else tc for tc in tool_calls]


class UvSystemMessage(UvMessage):
    """System-level message for instructions or context.

    Attributes:
        role: Always "system"
        content: System instructions or context
        metadata: Optional metadata
        message_id: Unique identifier
    """

    role: str = Field(default="system", frozen=True)

    def __init__(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ):
        """Initialize system message.

        Args:
            content: System instructions
            metadata: Optional metadata
            message_id: Optional message ID
        """
        init_data = {
            "role": "system",
            "content": content,
            "metadata": metadata or {},
        }
        if message_id:
            init_data["message_id"] = message_id
        super().__init__(**init_data)


class UvToolMessage(UvMessage):
    """Message containing tool execution results.

    Attributes:
        role: Always "tool"
        content: Tool execution result (typically JSON string or text)
        tool_call_id: ID of the tool call this responds to
        tool_name: Name of the tool that was executed
        metadata: Optional metadata (e.g., execution_time, status)
        message_id: Unique identifier
    """

    role: str = Field(default="tool", frozen=True)
    tool_call_id: str
    tool_name: str

    def __init__(
        self,
        content: Union[str, Dict[str, Any]],
        tool_call_id: str,
        tool_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
    ):
        """Initialize tool message.

        Args:
            content: Tool execution result
            tool_call_id: ID of the originating tool call
            tool_name: Name of the tool
            metadata: Optional metadata
            message_id: Optional message ID
        """
        init_data = {
            "role": "tool",
            "content": content,
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "metadata": metadata or {},
        }
        if message_id:
            init_data["message_id"] = message_id
        super().__init__(**init_data)


# Type alias for any message type
AnyMessage = Union[
    UvHumanMessage, UvAIMessage, UvSystemMessage, UvToolMessage, UvMessage
]

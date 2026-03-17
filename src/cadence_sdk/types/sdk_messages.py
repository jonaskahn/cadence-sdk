"""Framework-agnostic message types for Cadence SDK.

These message types provide a unified interface for agent communication
across different orchestration frameworks (LangGraph, OpenAI Agents, Google ADK).
"""

from abc import ABC
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UvMessage(BaseModel, ABC):
    """Base class for all Cadence SDK messages.

    Attributes:
        role: The role of the message sender (human, ai, system, tool)
        content: The message content (text or structured data)
        metadata: Optional metadata for extensibility
        message_id: Unique identifier for the message
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "role": "human",
                    "content": "Hello, how can you help me?",
                    "metadata": {},
                    "message_id": "123e4567-e89b-12d3-a456-426614174000",
                }
            ]
        }
    )

    role: str
    content: Union[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    message_id: str = Field(default_factory=lambda: str(uuid4()))

    @field_validator("metadata", mode="before")
    @classmethod
    def _normalize_metadata(cls, value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UvMessage":
        return cls.model_validate(data)


class UvHumanMessage(UvMessage):
    """Message from a human user.

    Attributes:
        role: Always "human"
        content: The user's message text
        metadata: Optional metadata (e.g., user_id, timestamp)
        message_id: Unique identifier
    """

    role: str = Field(default="human", frozen=True)


class ToolCall(BaseModel):
    """Represents a tool invocation request from an AI.

    Attributes:
        id: Unique identifier for this tool call
        name: Name of the tool to invoke
        args: Arguments to pass to the tool
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "call_abc123",
                    "name": "search_tool",
                    "args": {"query": "Python tutorials"},
                }
            ]
        }
    )

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    args: Dict[str, Any]


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

    @field_validator("tool_calls", mode="before")
    @classmethod
    def _normalize_tool_calls(
        cls, value: Optional[List[Union[ToolCall, Dict[str, Any]]]]
    ) -> List[ToolCall]:
        if not value:
            return []
        return [ToolCall(**tc) if isinstance(tc, dict) else tc for tc in value]


class UvSystemMessage(UvMessage):
    """System-level message for instructions or context.

    Attributes:
        role: Always "system"
        content: System instructions or context
        metadata: Optional metadata
        message_id: Unique identifier
    """

    role: str = Field(default="system", frozen=True)


class UvContextMessage(UvMessage):
    """Cached anchor context for grounded mode.

    Stored in conversation history after first fetch. On subsequent turns,
    the orchestrator extracts this instead of calling load_anchor() again.
    Filtered out before sending messages to the LLM — data is injected into
    the system prompt instead.
    """

    role: Literal["context"] = "context"
    content: Union[str, List[Dict[str, Any]]] = ""
    resource_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


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
        init_data: Dict[str, Any] = {
            "role": "tool",
            "content": content,
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "metadata": metadata,
        }
        if message_id is not None:
            init_data["message_id"] = message_id
        super().__init__(**init_data)


AnyMessage = Union[
    UvHumanMessage,
    UvAIMessage,
    UvSystemMessage,
    UvToolMessage,
    UvContextMessage,
    UvMessage,
]

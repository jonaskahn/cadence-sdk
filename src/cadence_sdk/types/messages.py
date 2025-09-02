"""Message types for Cadence plugins.

Re-exports LangChain message types for use in Cadence plugins.
"""

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

MessageTypes = {
    "BaseMessage": BaseMessage,
    "HumanMessage": HumanMessage,
    "AIMessage": AIMessage,
    "SystemMessage": SystemMessage,
    "ToolMessage": ToolMessage,
    "ChatMessage": ChatMessage,
}

__all__ = [
    "BaseMessage",
    "HumanMessage",
    "AIMessage",
    "SystemMessage",
    "ToolMessage",
    "ChatMessage",
    "MessageTypes",
]

"""State types for Cadence multi-agent system."""

from typing import Annotated, Any, Dict, Optional, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """TypedDict representing the conversation state tracked by the orchestrator.

    Replicates the core AgentState interface so plugins can use
    type hints without importing from the core system.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    thread_id: Optional[str]
    current_agent: Optional[str]
    agent_hops: Optional[int]
    plugin_context: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
    multi_agent: Optional[bool]

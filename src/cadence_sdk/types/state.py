"""State types for Cadence multi-agent system."""

from typing import Annotated, Any, Dict, List, Optional, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """TypedDict representing the conversation state tracked by the orchestrator.

    This replicates the core AgentState interface so plugins can use
    type hints without importing from the core system.

    Fields:
    - messages: Sequence of LangChain messages; aggregated via
      ``langgraph.graph.message.add_messages``.
    - current_agent: Identifier of the active agent/plugin for the current hop.
    - hops: Hop counter used to guard against infinite loops.
    - last_tool_call: Name of the last tool call issued by the assistant, if any.
    - session_id: Optional session identifier used to group requests.
    - metadata: Arbitrary metadata associated with the session or request.
    - agents_used: Ordered list of agents that have contributed so far.
    - parallel_results: Optional container for intermediate results produced
      outside the main turn.
    - routing_decision: Label of the most recent routing decision
      (e.g., next agent/tool).
    - plugin_context: Ephemeral plugin-specific context preserved across hops.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Optional[str]
    hops: int
    last_tool_call: Optional[str]
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]

    agents_used: List[str]
    parallel_results: Optional[Dict[str, Any]]
    routing_decision: Optional[str]

    plugin_context: Optional[Dict[str, Any]]

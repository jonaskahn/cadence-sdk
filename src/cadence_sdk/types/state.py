"""State types for Cadence multi-agent system."""

from typing import Annotated, Any, Dict, List, Optional, Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


class PluginContextFields:
    """Constants for plugin context field names to prevent typos."""

    ROUTING_HISTORY = "routing_history"
    CONSECUTIVE_AGENT_REPEATS = "consecutive_agent_repeats"
    LAST_ROUTED_AGENT = "last_routed_agent"
    SYNTHESIZER_OUTPUT = "synthesizer_output"
    TOOLS_USED = "tools_used"
    AGENT_OUTPUTS = "agent_outputs"
    SUSPENDED = "suspended"
    SYNTHESIZED = "synthesized"
    LAST_PLUGIN = "last_plugin"
    PLUGINS_WITH_SCHEMAS = "plugins_with_schemas"


class PluginContext(TypedDict, total=False):
    """Structured plugin context with defined schema."""

    routing_history: List[str]
    consecutive_agent_repeats: int
    last_routed_agent: Optional[str]
    synthesizer_output: Optional[Dict[str, Any]]
    tools_used: List[str]
    agent_outputs: Dict[str, Any]


class AgentStateFields:
    """Constants for AgentState field names to prevent typos."""

    MESSAGES = "messages"
    THREAD_ID = "thread_id"
    CURRENT_AGENT = "current_agent"
    AGENT_HOPS = "agent_hops"
    PLUGIN_CONTEXT = "plugin_context"
    METADATA = "metadata"
    MULTI_AGENT = "multi_agent"


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


class StateHelpers:
    """Helper functions for safe AgentState operations."""

    @staticmethod
    def safe_get_agent_hops(state: AgentState) -> int:
        """Safely get agent hops with default value."""
        hops = state.get(AgentStateFields.AGENT_HOPS, 0) or 0
        return max(0, hops)

    @staticmethod
    def safe_get_current_agent(state: AgentState) -> str:
        """Safely get current agent with default value."""
        return state.get(AgentStateFields.CURRENT_AGENT) or "coordinator"

    @staticmethod
    def safe_get_metadata(state: AgentState) -> Dict[str, Any]:
        """Safely get metadata with default value."""
        return state.get(AgentStateFields.METADATA, {}) or {}

    @staticmethod
    def safe_get_messages(state: AgentState) -> List[BaseMessage]:
        """Safely get messages with default value."""
        return state.get(AgentStateFields.MESSAGES, []) or []

    @staticmethod
    def get_plugin_context(state: AgentState) -> PluginContext:
        """Safely extract plugin context with defaults."""
        context = state.get(AgentStateFields.PLUGIN_CONTEXT, {}) or {}
        return {
            PluginContextFields.ROUTING_HISTORY: context.get(PluginContextFields.ROUTING_HISTORY, []),
            PluginContextFields.CONSECUTIVE_AGENT_REPEATS: context.get(
                PluginContextFields.CONSECUTIVE_AGENT_REPEATS, 0
            ),
            PluginContextFields.LAST_ROUTED_AGENT: context.get(PluginContextFields.LAST_ROUTED_AGENT),
            PluginContextFields.TOOLS_USED: context.get(PluginContextFields.TOOLS_USED, []),
            PluginContextFields.AGENT_OUTPUTS: context.get(PluginContextFields.AGENT_OUTPUTS, {}),
            PluginContextFields.SUSPENDED: context.get(PluginContextFields.SUSPENDED, False),
            PluginContextFields.SYNTHESIZED: context.get(PluginContextFields.SYNTHESIZED, False),
            **{
                k: v
                for k, v in context.items()
                if k
                not in {
                    PluginContextFields.ROUTING_HISTORY,
                    PluginContextFields.CONSECUTIVE_AGENT_REPEATS,
                    PluginContextFields.LAST_ROUTED_AGENT,
                    PluginContextFields.TOOLS_USED,
                    PluginContextFields.AGENT_OUTPUTS,
                    PluginContextFields.SUSPENDED,
                    PluginContextFields.SYNTHESIZED,
                }
            },
        }

    @staticmethod
    def update_plugin_context(state: AgentState, **updates) -> AgentState:
        """Update state with new plugin context values."""
        current_context = StateHelpers.get_plugin_context(state)
        updated_context = {**current_context, **updates}

        updated_state = dict(state)
        updated_state[AgentStateFields.PLUGIN_CONTEXT] = updated_context
        return updated_state

    @staticmethod
    def increment_agent_hops(state: AgentState, increment: int = 1) -> AgentState:
        """Safely increment agent hops."""
        current_hops = StateHelpers.safe_get_agent_hops(state)
        updated_state = dict(state)
        updated_state[AgentStateFields.AGENT_HOPS] = current_hops + increment
        return updated_state

    @staticmethod
    def create_state_update(
        message: BaseMessage, agent_hops: int, state: AgentState, preserve_keys: Optional[List[str]] = None
    ) -> AgentState:
        """Create standardized state update preserving important keys."""
        if preserve_keys is None:
            preserve_keys = [
                AgentStateFields.CURRENT_AGENT,
                AgentStateFields.PLUGIN_CONTEXT,
                AgentStateFields.THREAD_ID,
                AgentStateFields.METADATA,
                AgentStateFields.MULTI_AGENT,
            ]

        update: AgentState = {
            AgentStateFields.MESSAGES: [message],
            AgentStateFields.AGENT_HOPS: agent_hops,
        }

        for key in preserve_keys:
            if key in state:
                update[key] = state[key]

        return update


class RoutingHelpers:
    """Helper methods for plugin context routing logic."""

    @staticmethod
    def add_to_routing_history(context: PluginContext, agent_name: str) -> PluginContext:
        """Add agent to routing history."""
        updated_context = dict(context)
        if agent_name.strip() != "goto_finalize":
            history = list(context.get(PluginContextFields.ROUTING_HISTORY, []))
            history.append(agent_name)
            updated_context[PluginContextFields.ROUTING_HISTORY] = history
        return updated_context

    @staticmethod
    def add_tool_used(context: PluginContext, tool_name: str) -> PluginContext:
        """Add tool to used tools list."""
        updated_context = dict(context)
        tools = list(context.get(PluginContextFields.TOOLS_USED, []))
        if tool_name not in tools:
            tools.append(tool_name)
        updated_context[PluginContextFields.TOOLS_USED] = tools
        return updated_context

    @staticmethod
    def update_consecutive_routes(context: PluginContext, agent_name: str) -> PluginContext:
        """Update consecutive route counter based on agent selection."""
        updated_context = dict(context)

        if agent_name.startswith("goto_") and agent_name != "goto_finalize":
            selected_agent = agent_name[len("goto_") :]
            if context.get(PluginContextFields.LAST_ROUTED_AGENT) == selected_agent:
                updated_context[PluginContextFields.CONSECUTIVE_AGENT_REPEATS] = (
                    context.get(PluginContextFields.CONSECUTIVE_AGENT_REPEATS, 0) + 1
                )
            else:
                updated_context[PluginContextFields.CONSECUTIVE_AGENT_REPEATS] = 1
                updated_context[PluginContextFields.LAST_ROUTED_AGENT] = selected_agent
        else:
            updated_context[PluginContextFields.CONSECUTIVE_AGENT_REPEATS] = 0
            updated_context[PluginContextFields.LAST_ROUTED_AGENT] = None

        return updated_context


class StateValidation:
    """Optional validation helpers for development."""

    @staticmethod
    def validate_plugin_context(context: Dict[str, Any]) -> bool:
        """Validate plugin context structure."""
        try:
            # Try to create structured context
            StateHelpers.get_plugin_context({AgentStateFields.PLUGIN_CONTEXT: context})
            return True
        except Exception:
            return False

    @staticmethod
    def validate_state_structure(state: AgentState) -> bool:
        """Validate state has expected structure."""
        try:
            # Validate agent_hops is non-negative
            hops = StateHelpers.safe_get_agent_hops(state)
            if hops < 0:
                return False

            # Validate plugin_context structure
            StateHelpers.get_plugin_context(state)

            # Validate messages structure
            messages = StateHelpers.safe_get_messages(state)
            if not isinstance(messages, (list, tuple)):
                return False

            return True
        except Exception:
            return False

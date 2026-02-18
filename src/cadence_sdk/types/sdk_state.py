"""Framework-agnostic state definitions for Cadence SDK.

This module provides state management types and utilities that work
across different orchestration frameworks.
"""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

from .sdk_messages import AnyMessage


class PluginContext(TypedDict, total=False):
    """Plugin-specific context stored in state.

    Attributes:
        routing_history: List of agent names that have been routed to
        consecutive_agent_repeats: Count of consecutive routes to same agent
        last_routed_agent: Name of the last agent routed to
        synthesizer_output: Output from synthesizer node
        tools_used: List of tool names used in this conversation
        agent_outputs: Dict mapping agent names to their outputs
    """

    routing_history: List[str]
    consecutive_agent_repeats: int
    last_routed_agent: Optional[str]
    synthesizer_output: Optional[str]
    tools_used: List[str]
    agent_outputs: Dict[str, Any]


class UvState(TypedDict, total=False):
    """Universal state structure for Cadence orchestrators.

    This TypedDict provides a framework-agnostic state interface.
    All fields are optional (total=False) to support flexible state management.

    Attributes:
        messages: List of conversation messages
        thread_id: Conversation thread identifier
        current_agent: Name of currently active agent
        agent_hops: Number of agent transitions/hops
        plugin_context: Plugin-specific context data
        metadata: Additional arbitrary metadata
    """

    messages: List[AnyMessage]
    thread_id: Optional[str]
    current_agent: Optional[str]
    agent_hops: int
    plugin_context: PluginContext
    metadata: Dict[str, Any]


class AgentStateFields:
    """String constants for UvState field names.

    This class provides typed access to state field names to avoid
    hardcoded strings throughout the codebase.
    """

    MESSAGES = "messages"
    THREAD_ID = "thread_id"
    CURRENT_AGENT = "current_agent"
    AGENT_HOPS = "agent_hops"
    PLUGIN_CONTEXT = "plugin_context"
    METADATA = "metadata"


class PluginContextFields:
    """String constants for PluginContext field names."""

    ROUTING_HISTORY = "routing_history"
    CONSECUTIVE_AGENT_REPEATS = "consecutive_agent_repeats"
    LAST_ROUTED_AGENT = "last_routed_agent"
    SYNTHESIZER_OUTPUT = "synthesizer_output"
    TOOLS_USED = "tools_used"
    AGENT_OUTPUTS = "agent_outputs"


class StateHelpers:
    """Utility functions for safe state manipulation.

    These helpers provide type-safe access to state fields with
    proper defaults and null checking.
    """

    @staticmethod
    def safe_get_messages(state: UvState) -> List[AnyMessage]:
        """Get messages from state, returning empty list if not present."""
        return state.get(AgentStateFields.MESSAGES, [])

    @staticmethod
    def safe_get_thread_id(state: UvState) -> Optional[str]:
        """Get thread_id from state."""
        return state.get(AgentStateFields.THREAD_ID)

    @staticmethod
    def safe_get_current_agent(state: UvState) -> Optional[str]:
        """Get current_agent from state."""
        return state.get(AgentStateFields.CURRENT_AGENT)

    @staticmethod
    def safe_get_agent_hops(state: UvState) -> int:
        """Get agent_hops from state, defaulting to 0."""
        return state.get(AgentStateFields.AGENT_HOPS, 0)

    @staticmethod
    def safe_get_metadata(state: UvState) -> Dict[str, Any]:
        """Get metadata from state, returning empty dict if not present."""
        return state.get(AgentStateFields.METADATA, {})

    @staticmethod
    def get_plugin_context(state: UvState) -> PluginContext:
        """Get plugin_context from state, creating default if not present.

        Returns:
            PluginContext with sensible defaults
        """
        if AgentStateFields.PLUGIN_CONTEXT not in state:
            return PluginContext(
                routing_history=[],
                consecutive_agent_repeats=0,
                last_routed_agent=None,
                synthesizer_output=None,
                tools_used=[],
                agent_outputs={},
            )
        return state[AgentStateFields.PLUGIN_CONTEXT]

    @staticmethod
    def update_plugin_context(state: UvState, updates: Dict[str, Any]) -> UvState:
        """Update plugin_context fields in state.

        Args:
            state: Current state
            updates: Dict of fields to update in plugin_context

        Returns:
            New state with updated plugin_context
        """
        current_context = StateHelpers.get_plugin_context(state)
        updated_context = {**current_context, **updates}

        return {**state, AgentStateFields.PLUGIN_CONTEXT: updated_context}

    @staticmethod
    def increment_agent_hops(state: UvState) -> UvState:
        """Increment agent_hops counter.

        Args:
            state: Current state

        Returns:
            New state with incremented agent_hops
        """
        current_hops = StateHelpers.safe_get_agent_hops(state)
        return {**state, AgentStateFields.AGENT_HOPS: current_hops + 1}

    @staticmethod
    def create_state_update(**kwargs) -> UvState:
        """Create a state update dict with specified fields.

        Args:
            **kwargs: State fields to update

        Returns:
            UvState dict suitable for merging
        """
        return UvState(**kwargs)


class RoutingHelpers:
    """Helper functions for agent routing logic."""

    @staticmethod
    def add_to_routing_history(state: UvState, agent_name: str) -> UvState:
        """Add an agent to routing history.

        Args:
            state: Current state
            agent_name: Name of agent being routed to

        Returns:
            Updated state with agent added to routing history
        """
        context = StateHelpers.get_plugin_context(state)
        history = context.get(PluginContextFields.ROUTING_HISTORY, [])
        updated_history = history + [agent_name]

        last_agent = context.get(PluginContextFields.LAST_ROUTED_AGENT)
        repeats = RoutingHelpers._calculate_consecutive_repeats(
            last_agent, agent_name, context
        )

        return StateHelpers.update_plugin_context(
            state,
            {
                PluginContextFields.ROUTING_HISTORY: updated_history,
                PluginContextFields.LAST_ROUTED_AGENT: agent_name,
                PluginContextFields.CONSECUTIVE_AGENT_REPEATS: repeats,
            },
        )

    @staticmethod
    def _calculate_consecutive_repeats(
        last_agent: Optional[str], current_agent: str, context: Dict[str, Any]
    ) -> int:
        """Calculate consecutive agent repeats.

        Args:
            last_agent: Previously routed agent name
            current_agent: Current agent name
            context: Plugin context dictionary

        Returns:
            Number of consecutive repeats
        """
        if last_agent == current_agent:
            return context.get(PluginContextFields.CONSECUTIVE_AGENT_REPEATS, 0) + 1
        return 1

    @staticmethod
    def add_tool_used(state: UvState, tool_name: str) -> UvState:
        """Add a tool to the tools_used list.

        Args:
            state: Current state
            tool_name: Name of tool used

        Returns:
            Updated state
        """
        context = StateHelpers.get_plugin_context(state)
        tools = context.get(PluginContextFields.TOOLS_USED, [])
        updated_tools = RoutingHelpers._add_tool_avoiding_duplicates(tools, tool_name)

        return StateHelpers.update_plugin_context(
            state, {PluginContextFields.TOOLS_USED: updated_tools}
        )

    @staticmethod
    def _add_tool_avoiding_duplicates(tools: List[str], tool_name: str) -> List[str]:
        """Add tool to list if not already present.

        Args:
            tools: Existing tools list
            tool_name: Tool name to add

        Returns:
            Updated tools list
        """
        if tool_name not in tools:
            return tools + [tool_name]
        return tools

    @staticmethod
    def update_consecutive_routes(state: UvState, agent_name: str) -> int:
        """Get consecutive route count for an agent.

        Args:
            state: Current state
            agent_name: Agent being checked

        Returns:
            Number of consecutive routes to this agent
        """
        context = StateHelpers.get_plugin_context(state)
        last_agent = context.get(PluginContextFields.LAST_ROUTED_AGENT)

        if last_agent == agent_name:
            return context.get(PluginContextFields.CONSECUTIVE_AGENT_REPEATS, 0)
        else:
            return 0


def merge_messages(
    existing: List[AnyMessage], new: List[AnyMessage], deduplicate: bool = True
) -> List[AnyMessage]:
    """Merge two message lists, optionally deduplicating by message_id.

    Args:
        existing: Existing message list
        new: New messages to add
        deduplicate: Whether to remove duplicate message_ids (default True)

    Returns:
        Merged message list
    """
    if not deduplicate:
        return existing + new

    return _merge_messages_with_deduplication(existing, new)


def _merge_messages_with_deduplication(
    existing: List[AnyMessage], new: List[AnyMessage]
) -> List[AnyMessage]:
    """Merge message lists avoiding duplicate message IDs.

    Args:
        existing: Existing message list
        new: New messages to add

    Returns:
        Merged message list without duplicates
    """
    seen_ids = {msg.message_id for msg in existing}
    result = list(existing)

    for msg in new:
        if msg.message_id not in seen_ids:
            result.append(msg)
            seen_ids.add(msg.message_id)

    return result


def create_initial_state(
    messages: Optional[List[AnyMessage]] = None,
    thread_id: Optional[str] = None,
    **kwargs,
) -> UvState:
    """Create an initial state with sensible defaults.

    Args:
        messages: Initial messages (default empty)
        thread_id: Thread identifier
        **kwargs: Additional state fields

    Returns:
        UvState with defaults
    """
    state = UvState(
        messages=messages or [],
        thread_id=thread_id,
        agent_hops=0,
        plugin_context=PluginContext(
            routing_history=[],
            consecutive_agent_repeats=0,
            last_routed_agent=None,
            synthesizer_output=None,
            tools_used=[],
            agent_outputs={},
        ),
        metadata={},
    )

    state.update(kwargs)
    return state

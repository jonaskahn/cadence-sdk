"""Tests for SDK state types and helpers."""

from cadence_sdk import (
    AgentStateFields,
    PluginContextFields,
    RoutingHelpers,
    StateHelpers,
    UvHumanMessage,
    create_initial_state,
    merge_messages,
)


class TestAgentStateFields:
    """Tests for AgentStateFields constants."""

    def test_field_names_are_defined(self):
        """AgentStateFields defines expected field names."""
        assert AgentStateFields.MESSAGES == "messages"
        assert AgentStateFields.THREAD_ID == "thread_id"
        assert AgentStateFields.CURRENT_AGENT == "current_agent"
        assert AgentStateFields.AGENT_HOPS == "agent_hops"
        assert AgentStateFields.PLUGIN_CONTEXT == "plugin_context"
        assert AgentStateFields.METADATA == "metadata"


class TestPluginContextFields:
    """Tests for PluginContextFields constants."""

    def test_field_names_are_defined(self):
        """PluginContextFields defines expected field names."""
        assert PluginContextFields.ROUTING_HISTORY == "routing_history"
        assert (
            PluginContextFields.CONSECUTIVE_AGENT_REPEATS == "consecutive_agent_repeats"
        )
        assert PluginContextFields.LAST_ROUTED_AGENT == "last_routed_agent"
        assert PluginContextFields.TOOLS_USED == "tools_used"


class TestCreateInitialState:
    """Tests for create_initial_state."""

    def test_creates_state_with_defaults(self):
        """create_initial_state returns state with sensible defaults."""
        state = create_initial_state()
        assert state.get("messages") == []
        assert state.get("agent_hops") == 0
        assert "plugin_context" in state
        assert state.get("metadata") == {}

    def test_accepts_messages_and_thread_id(self):
        """create_initial_state accepts messages and thread_id."""
        msg = UvHumanMessage(content="Hello")
        state = create_initial_state(
            messages=[msg],
            thread_id="thread_123",
        )
        assert StateHelpers.safe_get_messages(state) == [msg]
        assert StateHelpers.safe_get_thread_id(state) == "thread_123"

    def test_accepts_additional_kwargs(self):
        """create_initial_state accepts additional state fields."""
        state = create_initial_state(custom_field="value")
        assert state.get("custom_field") == "value"


class TestStateHelpers:
    """Tests for StateHelpers utility methods."""

    def test_safe_get_messages_returns_empty_list_when_missing(self):
        """safe_get_messages returns [] when messages not in state."""
        state = {}
        assert StateHelpers.safe_get_messages(state) == []

    def test_safe_get_thread_id_returns_none_when_missing(self):
        """safe_get_thread_id returns None when thread_id not in state."""
        state = {}
        assert StateHelpers.safe_get_thread_id(state) is None

    def test_safe_get_agent_hops_returns_zero_when_missing(self):
        """safe_get_agent_hops returns 0 when agent_hops not in state."""
        state = {}
        assert StateHelpers.safe_get_agent_hops(state) == 0

    def test_get_plugin_context_creates_default_when_missing(self):
        """get_plugin_context creates default context when not in state."""
        state = {}
        context = StateHelpers.get_plugin_context(state)
        assert context.get("routing_history") == []
        assert context.get("consecutive_agent_repeats") == 0
        assert context.get("tools_used") == []

    def test_increment_agent_hops(self):
        """increment_agent_hops increments counter."""
        state = create_initial_state()
        state = StateHelpers.increment_agent_hops(state)
        assert StateHelpers.safe_get_agent_hops(state) == 1
        state = StateHelpers.increment_agent_hops(state)
        assert StateHelpers.safe_get_agent_hops(state) == 2

    def test_update_plugin_context(self):
        """update_plugin_context merges updates into context."""
        state = create_initial_state()
        state = StateHelpers.update_plugin_context(
            state,
            {"last_routed_agent": "agent1"},
        )
        context = StateHelpers.get_plugin_context(state)
        assert context.get("last_routed_agent") == "agent1"


class TestRoutingHelpers:
    """Tests for RoutingHelpers."""

    def test_add_to_routing_history(self):
        """add_to_routing_history appends agent to history."""
        state = create_initial_state()
        state = RoutingHelpers.add_to_routing_history(state, "agent1")
        state = RoutingHelpers.add_to_routing_history(state, "agent2")

        context = StateHelpers.get_plugin_context(state)
        assert context.get("routing_history") == ["agent1", "agent2"]
        assert context.get("last_routed_agent") == "agent2"

    def test_add_to_routing_history_tracks_consecutive_repeats(self):
        """add_to_routing_history tracks consecutive routes to same agent."""
        state = create_initial_state()
        state = RoutingHelpers.add_to_routing_history(state, "agent1")
        state = RoutingHelpers.add_to_routing_history(state, "agent1")

        context = StateHelpers.get_plugin_context(state)
        assert context.get("consecutive_agent_repeats") == 2

    def test_add_tool_used(self):
        """add_tool_used appends tool to tools_used list."""
        state = create_initial_state()
        state = RoutingHelpers.add_tool_used(state, "search")
        state = RoutingHelpers.add_tool_used(state, "fetch")

        context = StateHelpers.get_plugin_context(state)
        assert "search" in context.get("tools_used", [])
        assert "fetch" in context.get("tools_used", [])

    def test_add_tool_used_avoids_duplicates(self):
        """add_tool_used does not add duplicate tool names."""
        state = create_initial_state()
        state = RoutingHelpers.add_tool_used(state, "search")
        state = RoutingHelpers.add_tool_used(state, "search")

        context = StateHelpers.get_plugin_context(state)
        tools = context.get("tools_used", [])
        assert tools.count("search") == 1

    def test_update_consecutive_routes_returns_count_for_matching_agent(self):
        """update_consecutive_routes returns count when agent matches last."""
        state = create_initial_state()
        state = RoutingHelpers.add_to_routing_history(state, "agent1")
        state = RoutingHelpers.add_to_routing_history(state, "agent1")

        count = RoutingHelpers.update_consecutive_routes(state, "agent1")
        assert count == 2

    def test_update_consecutive_routes_returns_zero_for_different_agent(self):
        """update_consecutive_routes returns 0 when agent differs from last."""
        state = create_initial_state()
        state = RoutingHelpers.add_to_routing_history(state, "agent1")

        count = RoutingHelpers.update_consecutive_routes(state, "agent2")
        assert count == 0


class TestMergeMessages:
    """Tests for merge_messages."""

    def test_merge_concatenates_when_deduplicate_false(self):
        """merge_messages concatenates when deduplicate is False."""
        msg1 = UvHumanMessage(content="A", message_id="id1")
        msg2 = UvHumanMessage(content="B", message_id="id2")
        result = merge_messages([msg1], [msg2], deduplicate=False)
        assert len(result) == 2
        assert result[0].content == "A"
        assert result[1].content == "B"

    def test_merge_deduplicates_by_message_id(self):
        """merge_messages deduplicates by message_id when deduplicate is True."""
        msg1 = UvHumanMessage(content="A", message_id="same_id")
        msg2 = UvHumanMessage(content="B", message_id="same_id")
        result = merge_messages([msg1], [msg2], deduplicate=True)
        assert len(result) == 1
        assert result[0].content == "A"

    def test_merge_keeps_distinct_messages(self):
        """merge_messages keeps messages with distinct ids."""
        msg1 = UvHumanMessage(content="A", message_id="id1")
        msg2 = UvHumanMessage(content="B", message_id="id2")
        result = merge_messages([msg1], [msg2], deduplicate=True)
        assert len(result) == 2

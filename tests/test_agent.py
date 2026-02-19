"""Tests for BaseAgent."""

from cadence_sdk import BaseAgent, UvTool


class TestBaseAgentInterface:
    """Tests for BaseAgent interface."""

    def test_minimal_agent_returns_tools(self, minimal_agent):
        """MinimalAgent returns list of UvTool instances."""
        tools = minimal_agent.get_tools()
        assert isinstance(tools, list)
        assert len(tools) == 1
        assert isinstance(tools[0], UvTool)
        assert tools[0].name == "echo"

    def test_minimal_agent_returns_system_prompt(self, minimal_agent):
        """MinimalAgent returns non-empty system prompt."""
        prompt = minimal_agent.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "minimal" in prompt.lower()

    def test_agent_initialize_accepts_config(self, minimal_agent):
        """Agent initialize accepts config dict without raising."""
        minimal_agent.initialize({"key": "value"})

    def test_agent_get_settings_schema_returns_empty_by_default(self, minimal_agent):
        """Default get_settings_schema returns empty list."""
        schema = minimal_agent.get_settings_schema()
        assert schema == []

    def test_agent_repr_includes_class_name(self, minimal_agent):
        """Agent __repr__ includes class name."""
        repr_str = repr(minimal_agent)
        assert "MinimalAgent" in repr_str


class TestAgentToolExecution:
    """Tests for agent tool invocation."""

    def test_echo_tool_returns_input(self, minimal_agent):
        """Echo tool returns the input text."""
        tools = minimal_agent.get_tools()
        echo_tool = tools[0]
        result = echo_tool.invoke(text="hello")
        assert result == "hello"

    def test_plugin_create_agent_returns_fresh_instance(self, minimal_plugin):
        """Each create_agent call returns a new agent instance."""
        agent1 = minimal_plugin.create_agent()
        agent2 = minimal_plugin.create_agent()
        assert agent1 is not agent2


class TestAgentFromPlugin:
    """Tests for agent creation from plugin."""

    def test_plugin_create_agent_returns_base_agent(self, minimal_plugin):
        """Plugin create_agent returns BaseAgent instance."""
        agent = minimal_plugin.create_agent()
        assert isinstance(agent, BaseAgent)

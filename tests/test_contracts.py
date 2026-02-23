"""Tests for PluginContract."""

import pytest
from cadence_sdk import PluginContract


class TestPluginContractCreation:
    """Tests for PluginContract construction."""

    def test_wraps_plugin_class(self, minimal_plugin):
        """PluginContract wraps plugin class and exposes metadata."""
        contract = PluginContract(minimal_plugin)
        assert contract.plugin_class is minimal_plugin
        assert contract.pid == "com.test.minimal"
        assert contract.name == "Minimal Plugin"
        assert contract.version == "1.0.0"
        assert contract.description == "Minimal plugin for tests"
        assert contract.capabilities == ["echo"]
        assert contract.agent_type == "specialized"
        assert contract.is_stateless is True

    def test_rejects_non_base_plugin_class(self):
        """PluginContract raises TypeError for non-BasePlugin class."""

        class NotAPlugin:
            pass

        with pytest.raises(TypeError, match="must inherit from BasePlugin"):
            PluginContract(NotAPlugin)

    def test_metadata_is_cached(self, minimal_plugin):
        """PluginContract caches metadata on first access."""
        contract = PluginContract(minimal_plugin)
        meta1 = contract.metadata
        meta2 = contract.metadata
        assert meta1 is meta2


class TestPluginContractMethods:
    """Tests for PluginContract methods."""

    def test_create_agent_returns_agent(self, minimal_plugin):
        """create_agent returns BaseAgent instance."""
        contract = PluginContract(minimal_plugin)
        agent = contract.create_agent()
        assert agent is not None
        assert hasattr(agent, "get_tools")
        assert hasattr(agent, "get_system_prompt")

    def test_validate_dependencies_delegates_to_plugin(self, minimal_plugin):
        """validate_dependencies delegates to plugin."""
        contract = PluginContract(minimal_plugin)
        errors = contract.validate_dependencies()
        assert errors == []

    def test_health_check_delegates_to_plugin(self, minimal_plugin):
        """health_check delegates to plugin."""
        contract = PluginContract(minimal_plugin)
        result = contract.health_check()
        assert "status" in result


class TestPluginContractEquality:
    """Tests for PluginContract equality and hashing."""

    def test_equal_contracts_same_pid_and_version(self, minimal_plugin):
        """Two contracts with same pid and version are equal."""
        c1 = PluginContract(minimal_plugin)
        c2 = PluginContract(minimal_plugin)
        assert c1 == c2
        assert hash(c1) == hash(c2)

    def test_contracts_can_be_used_in_set(self, minimal_plugin):
        """PluginContracts are hashable and can be used in sets."""
        c1 = PluginContract(minimal_plugin)
        c2 = PluginContract(minimal_plugin)
        s = {c1, c2}
        assert len(s) == 1

    def test_unequal_to_non_contract(self, minimal_plugin):
        """PluginContract is not equal to non-PluginContract."""
        contract = PluginContract(minimal_plugin)
        assert contract != "not a contract"
        assert contract != None  # noqa: E711

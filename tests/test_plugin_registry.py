"""Tests for PluginRegistry and register_plugin."""

import pytest
from cadence_sdk import PluginContract, PluginRegistry, register_plugin

from .conftest import MinimalPluginV2


class TestPluginRegistrySingleton:
    """Tests for PluginRegistry singleton behavior."""

    def test_instance_returns_same_registry(self):
        """PluginRegistry.instance() returns same instance."""
        r1 = PluginRegistry.instance()
        r2 = PluginRegistry.instance()
        assert r1 is r2


class TestPluginRegistration:
    """Tests for plugin registration."""

    def test_register_plugin_returns_contract(self, plugin_registry, minimal_plugin):
        """register_plugin returns PluginContract for valid plugin."""
        contract = plugin_registry.register(minimal_plugin)
        assert isinstance(contract, PluginContract)
        assert contract.pid == "com.test.minimal"

    def test_register_plugin_convenience_function(
        self, plugin_registry, minimal_plugin
    ):
        """register_plugin convenience function works."""
        contract = register_plugin(minimal_plugin)
        assert isinstance(contract, PluginContract)
        assert plugin_registry.has_plugin("com.test.minimal")

    def test_registry_rejects_non_base_plugin(self, plugin_registry):
        """Registry raises TypeError for non-BasePlugin class."""

        class NotAPlugin:
            pass

        with pytest.raises(TypeError, match="must inherit from BasePlugin"):
            plugin_registry.register(NotAPlugin)


class TestPluginRegistryLookup:
    """Tests for plugin lookup methods."""

    def test_get_plugin_returns_registered_plugin(
        self, plugin_registry, minimal_plugin
    ):
        """get_plugin returns contract for registered pid."""
        plugin_registry.register(minimal_plugin)
        contract = plugin_registry.get_plugin("com.test.minimal")
        assert contract is not None
        assert contract.pid == "com.test.minimal"

    def test_get_plugin_returns_none_for_unknown_pid(self, plugin_registry):
        """get_plugin returns None for unregistered pid."""
        assert plugin_registry.get_plugin("com.unknown.plugin") is None

    def test_has_plugin_returns_true_when_registered(
        self, plugin_registry, minimal_plugin
    ):
        """has_plugin returns True for registered plugin."""
        plugin_registry.register(minimal_plugin)
        assert plugin_registry.has_plugin("com.test.minimal") is True

    def test_has_plugin_returns_false_when_not_registered(self, plugin_registry):
        """has_plugin returns False for unregistered plugin."""
        assert plugin_registry.has_plugin("com.unknown.plugin") is False

    def test_list_registered_plugins_returns_all(self, plugin_registry, minimal_plugin):
        """list_registered_plugins returns all registered plugins."""
        plugin_registry.register(minimal_plugin)
        plugins = plugin_registry.list_registered_plugins()
        assert len(plugins) == 1
        assert plugins[0].pid == "com.test.minimal"

    def test_get_all_ids_returns_pid_list(self, plugin_registry, minimal_plugin):
        """get_all_ids returns list of registered pids."""
        plugin_registry.register(minimal_plugin)
        ids = plugin_registry.get_all_ids()
        assert ids == ["com.test.minimal"]


class TestPluginRegistryVersionConflict:
    """Tests for version conflict resolution."""

    def test_registry_keeps_higher_version_on_duplicate_pid(
        self, plugin_registry, minimal_plugin
    ):
        """Registry keeps higher version when same pid registered twice."""
        plugin_registry.register(minimal_plugin)
        plugin_registry.register(MinimalPluginV2)

        contract = plugin_registry.get_plugin("com.test.minimal")
        assert contract.version == "2.0.0"

    def test_override_replaces_registration_regardless_of_version(
        self, plugin_registry, minimal_plugin
    ):
        """Override=True replaces existing registration with any version."""
        plugin_registry.register(MinimalPluginV2)
        plugin_registry.register(minimal_plugin, override=True)

        contract = plugin_registry.get_plugin("com.test.minimal")
        assert contract.version == "1.0.0"


class TestPluginRegistryFiltering:
    """Tests for capability and type filtering."""

    def test_list_plugins_by_capability(self, plugin_registry, minimal_plugin):
        """list_plugins_by_capability filters by capability tag."""
        plugin_registry.register(minimal_plugin)
        plugins = plugin_registry.list_plugins_by_capability("echo")
        assert len(plugins) == 1
        assert "echo" in plugins[0].capabilities

    def test_list_plugins_by_capability_returns_empty_for_no_match(
        self, plugin_registry, minimal_plugin
    ):
        """list_plugins_by_capability returns empty for non-matching capability."""
        plugin_registry.register(minimal_plugin)
        plugins = plugin_registry.list_plugins_by_capability("nonexistent")
        assert plugins == []

    def test_list_plugins_by_type(self, plugin_registry, minimal_plugin):
        """list_plugins_by_type filters by agent_type."""
        plugin_registry.register(minimal_plugin)
        plugins = plugin_registry.list_plugins_by_type("specialized")
        assert len(plugins) == 1


class TestPluginRegistryUnregister:
    """Tests for plugin unregistration."""

    def test_unregister_removes_plugin(self, plugin_registry, minimal_plugin):
        """unregister removes plugin and returns True."""
        plugin_registry.register(minimal_plugin)
        result = plugin_registry.unregister("com.test.minimal")
        assert result is True
        assert plugin_registry.get_plugin("com.test.minimal") is None

    def test_unregister_returns_false_for_unknown_pid(self, plugin_registry):
        """unregister returns False when pid not found."""
        result = plugin_registry.unregister("com.unknown.plugin")
        assert result is False


class TestPluginRegistryClear:
    """Tests for clear_all."""

    def test_clear_all_removes_all_plugins(self, plugin_registry, minimal_plugin):
        """clear_all removes all registered plugins."""
        plugin_registry.register(minimal_plugin)
        plugin_registry.clear_all()
        assert plugin_registry.get_plugin("com.test.minimal") is None
        assert plugin_registry.list_registered_plugins() == []

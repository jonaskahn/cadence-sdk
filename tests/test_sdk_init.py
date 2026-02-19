"""Tests for cadence_sdk package initialization and public API."""


class TestSdkImports:
    """Tests for SDK public API imports."""

    def test_version_is_defined(self):
        """__version__ is defined and is string."""
        from cadence_sdk import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_base_classes_importable(self):
        """Base classes are importable from cadence_sdk."""
        from cadence_sdk import BaseAgent, BasePlugin, Loggable, PluginMetadata

        assert BaseAgent is not None
        assert BasePlugin is not None
        assert Loggable is not None
        assert PluginMetadata is not None

    def test_message_types_importable(self):
        """Message types are importable from cadence_sdk."""
        from cadence_sdk import (
            ToolCall,
            UvAIMessage,
            UvHumanMessage,
            UvSystemMessage,
            UvToolMessage,
        )

        assert UvHumanMessage is not None
        assert UvAIMessage is not None
        assert UvSystemMessage is not None
        assert UvToolMessage is not None
        assert ToolCall is not None

    def test_tools_importable(self):
        """Tool types are importable from cadence_sdk."""
        from cadence_sdk import CacheConfig, UvTool, uvtool

        assert UvTool is not None
        assert uvtool is not None
        assert CacheConfig is not None

    def test_state_importable(self):
        """State types and helpers are importable from cadence_sdk."""
        from cadence_sdk import (
            RoutingHelpers,
            StateHelpers,
            create_initial_state,
            merge_messages,
        )

        assert StateHelpers is not None
        assert RoutingHelpers is not None
        assert create_initial_state is not None
        assert merge_messages is not None

    def test_registry_importable(self):
        """Registry is importable from cadence_sdk."""
        from cadence_sdk import PluginContract, PluginRegistry, register_plugin

        assert PluginRegistry is not None
        assert PluginContract is not None
        assert register_plugin is not None

    def test_utils_importable(self):
        """Utilities are importable from cadence_sdk."""
        from cadence_sdk import (
            DirectoryPluginDiscovery,
            discover_plugins,
            validate_plugin_structure,
            validate_plugin_structure_shallow,
        )

        assert validate_plugin_structure is not None
        assert validate_plugin_structure_shallow is not None
        assert DirectoryPluginDiscovery is not None
        assert discover_plugins is not None

    def test_decorators_importable(self):
        """Decorators are importable from cadence_sdk."""
        from cadence_sdk import plugin_settings

        assert plugin_settings is not None

"""Tests for BasePlugin."""

from cadence_sdk import BasePlugin, PluginMetadata
from cadence_sdk.base.agent import BaseAgent
from cadence_sdk.base.plugin import BasePlugin as BasePluginClass

from .conftest import MinimalPlugin


class TestBasePluginInterface:
    """Tests for BasePlugin abstract interface."""

    def test_minimal_plugin_implements_required_methods(self, minimal_plugin):
        """MinimalPlugin implements get_metadata and create_agent."""
        metadata = minimal_plugin.get_metadata()
        assert isinstance(metadata, PluginMetadata)
        assert metadata.pid == "com.test.minimal"

        agent = minimal_plugin.create_agent()
        assert isinstance(agent, BaseAgent)

    def test_validate_dependencies_returns_empty_by_default(self, minimal_plugin):
        """Default validate_dependencies returns empty list."""
        errors = minimal_plugin.validate_dependencies()
        assert errors == []

    def test_health_check_returns_unknown_by_default(self, minimal_plugin):
        """Default health_check returns status unknown."""
        result = minimal_plugin.health_check()
        assert result == {"status": "unknown"}

    def test_plugin_repr_includes_name_and_version(self, minimal_plugin):
        """Plugin __repr__ includes metadata when available."""
        repr_str = repr(minimal_plugin())
        assert "MinimalPlugin" in repr_str
        assert "Minimal Plugin" in repr_str
        assert "1.0.0" in repr_str


class TestBasePluginSubclass:
    """Tests for BasePlugin inheritance."""

    def test_minimal_plugin_is_base_plugin_subclass(self):
        """MinimalPlugin inherits from BasePlugin."""
        assert issubclass(MinimalPlugin, BasePluginClass)
        assert issubclass(MinimalPlugin, BasePlugin)

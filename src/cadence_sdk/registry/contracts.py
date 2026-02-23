"""Plugin contract wrapper for standardized interface."""

from typing import Optional, Type

from ..base import BaseAgent, BasePlugin, PluginMetadata


class PluginContract:
    """Wrapper providing standardized interface to plugin classes.

    The PluginContract wraps a plugin class and provides a consistent
    interface for the framework to interact with plugins, regardless
    of implementation details.

    This abstraction allows plugins to evolve independently while
    maintaining a stable contract with the framework.

    Attributes:
        plugin_class: The plugin class being wrapped
        metadata: Cached metadata from plugin
    """

    def __init__(self, plugin_class: Type[BasePlugin]):
        """Initialize plugin contract.

        Args:
            plugin_class: The plugin class to wrap
        """
        if not issubclass(plugin_class, BasePlugin):
            raise TypeError(f"{plugin_class.__name__} must inherit from BasePlugin")

        self.plugin_class = plugin_class
        self._metadata: Optional[PluginMetadata] = None

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata (cached).

        Returns:
            PluginMetadata instance
        """
        if self._metadata is None:
            self._metadata = self.plugin_class.get_metadata()
        return self._metadata

    @property
    def pid(self) -> str:
        """Get the globally unique plugin identifier (reverse-domain).

        This is the primary key used by the PluginRegistry. It must follow
        reverse-domain naming convention (e.g., "com.example.product_search").
        """
        return self.metadata.pid

    @property
    def name(self) -> str:
        """Get plugin display name.

        This is the human-readable label, overridable per orchestrator
        instance in Tier 4 node_settings.
        """
        return self.metadata.name

    @property
    def version(self) -> str:
        """Get plugin version."""
        return self.metadata.version

    @property
    def description(self) -> str:
        """Get plugin description."""
        return self.metadata.description

    @property
    def capabilities(self) -> list[str]:
        """Get plugin capabilities."""
        return self.metadata.capabilities

    @property
    def agent_type(self) -> str:
        """Get plugin agent type."""
        return self.metadata.agent_type

    @property
    def is_stateless(self) -> bool:
        """Check if plugin is stateless."""
        return self.metadata.stateless

    def create_agent(self) -> BaseAgent:
        """Create a new agent instance.

        Returns:
            BaseAgent instance
        """
        return self.plugin_class.create_agent()

    def validate_dependencies(self) -> list[str]:
        """Validate plugin dependencies.

        Returns:
            List of error messages (empty if OK)
        """
        return self.plugin_class.validate_dependencies()

    def health_check(self) -> dict:
        """Perform health check.

        Returns:
            Health status dictionary
        """
        return self.plugin_class.health_check()

    def __repr__(self) -> str:
        """String representation."""
        return f"PluginContract(pid='{self.pid}', version='{self.version}')"

    def __eq__(self, other) -> bool:
        """Equality comparison based on pid and version."""
        if not isinstance(other, PluginContract):
            return False
        return self.pid == other.pid and self.version == other.version

    def __hash__(self) -> int:
        """Hash based on pid and version."""
        return hash((self.pid, self.version))

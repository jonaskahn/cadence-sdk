"""Plugin contracts for communication between core and plugins."""

from typing import Any, Type

from ..base.agent import BaseAgent
from ..base.metadata import PluginMetadata
from ..base.plugin import BasePlugin


class PluginContract:
    """Contract defining the interface between Cadence core and a plugin.

    Wraps a plugin class and provides a standardized interface
    for the Cadence core system to interact with plugins without directly
    importing or instantiating them.
    """

    def __init__(self, plugin_class: Type[BasePlugin]):
        """Initialize the plugin contract.

        Args:
            plugin_class: The plugin class that implements BasePlugin
        """
        self.plugin_class = plugin_class
        self._metadata = None
        self._validated = False

    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            PluginMetadata: Plugin metadata
        """
        if self._metadata is None:
            self._metadata = self.plugin_class.get_metadata()
        return self._metadata

    def create_agent(self) -> BaseAgent:
        """Create an agent instance.

        Returns:
            BaseAgent: New agent instance
        """
        return self.plugin_class.create_agent()

    def validate_dependencies(self) -> list[str]:
        """Validate plugin dependencies.

        Returns:
            list[str]: List of validation errors (empty if valid)
        """
        return self.plugin_class.validate_dependencies()

    def get_config_schema(self) -> dict[str, Any]:
        """Get plugin configuration schema.

        Returns:
            dict[str, Any]: Configuration schema
        """
        return self.plugin_class.get_config_schema()

    def health_check(self) -> dict[str, Any]:
        """Perform plugin health check.

        Returns:
            dict[str, Any]: Health status
        """
        return self.plugin_class.health_check()

    def is_valid(self) -> bool:
        """Check if plugin contract is valid.

        Returns:
            bool: True if plugin is valid, False otherwise
        """
        if self._validated:
            return True

        try:
            metadata = self.get_metadata()
            if not metadata.name or not metadata.version:
                return False

            errors = self.validate_dependencies()
            if errors:
                return False

            agent = self.create_agent()
            if not isinstance(agent, BaseAgent):
                return False

            self._validated = True
            return True
        except Exception:
            return False

    @property
    def name(self) -> str:
        """Get plugin name.

        Returns:
            str: Plugin name
        """
        return self.get_metadata().name

    @property
    def version(self) -> str:
        """Get plugin version.

        Returns:
            str: Plugin version
        """
        return self.get_metadata().version

    def __str__(self) -> str:
        """String representation of the contract.

        Returns:
            str: Contract description
        """
        metadata = self.get_metadata()
        return f"PluginContract({metadata.name} v{metadata.version})"

    def __repr__(self) -> str:
        """Detailed string representation.

        Returns:
            str: Detailed contract description
        """
        return f"PluginContract(plugin_class={self.plugin_class.__name__}, name={self.name}, version={self.version})"

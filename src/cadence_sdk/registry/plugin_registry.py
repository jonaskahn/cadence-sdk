"""Plugin registry for discovering and managing plugins."""

from typing import Any, Dict, List, Optional, Type

from packaging.version import Version

from ..base.loggable import Loggable
from ..base.plugin import BasePlugin
from .contracts import PluginContract


class PluginRegistry(Loggable):
    """Registry that tracks and manages discovered plugins."""

    def __init__(self):
        super().__init__()
        self._plugins: Dict[str, PluginContract] = {}
        self._plugin_classes: Dict[str, Type[BasePlugin]] = {}

    def get_plugin(self, plugin_name: str) -> Optional[PluginContract]:
        """Get a plugin contract.

        Args:
            plugin_name: Plugin name.

        Returns:
            Optional[PluginContract]: Contract if found, else None.
        """
        return self._plugins.get(plugin_name)

    def list_registered_plugins(self) -> List[PluginContract]:
        """Return all registered plugin contracts."""
        return list(self._plugins.values())

    def list_plugin_names(self) -> List[str]:
        """Return all registered plugin names."""
        return list(self._plugins.keys())

    def list_plugins_by_capability(self, capability: str) -> List[PluginContract]:
        """Return plugins that support a capability."""
        matching_plugins = []
        for contract in self._plugins.values():
            metadata = contract.get_metadata()
            if capability in metadata.capabilities:
                matching_plugins.append(contract)
        return matching_plugins

    def list_plugins_by_type(self, agent_type: str) -> List[PluginContract]:
        """Return plugins by agent type."""
        matching_plugins = []
        for contract in self._plugins.values():
            metadata = contract.get_metadata()
            if metadata.agent_type == agent_type:
                matching_plugins.append(contract)
        return matching_plugins

    def run_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """Run health checks for all plugins."""
        health_results = {}
        for plugin_name, contract in self._plugins.items():
            try:
                status = contract.health_check()
                health_results[plugin_name] = status
            except Exception as e:
                health_results[plugin_name] = {"healthy": False, "error": str(e)}
                self.logger.error(f"Health check failed for plugin {plugin_name}: {e}")
        return health_results

    def unregister(self, plugin_name: str) -> bool:
        """Unregister a plugin.

        Args:
            plugin_name: Plugin name.

        Returns:
            bool: True if unregistered, False otherwise.
        """
        if plugin_name in self._plugins:
            del self._plugins[plugin_name]
            del self._plugin_classes[plugin_name]
            self.logger.info(f"Unregistered plugin: {plugin_name}")
            return True
        return False

    def clear_all(self) -> None:
        """Clear the registry."""
        self._plugins.clear()
        self._plugin_classes.clear()
        self.logger.info("Cleared all plugins from registry")

    def register(self, plugin_class: Type[BasePlugin]) -> None:
        """Register a plugin class.

        Args:
            plugin_class: Class implementing `BasePlugin`.

        Raises:
            ValueError: If registration fails.
        """
        try:
            contract = PluginContract(plugin_class)
            self._validate_plugin_before_registration(plugin_class)

            plugin_metadata = contract.get_metadata()
            plugin_name = plugin_metadata.name

            if not self._should_skip_registration(plugin_name, plugin_class, plugin_metadata):
                self._complete_plugin_registration(plugin_name, plugin_class, contract, plugin_metadata)

        except Exception as e:
            self.logger.error(f"Failed to register plugin {plugin_class.__name__}: {e}")
            raise ValueError(f"Plugin registration failed: {e}") from e

    def _validate_plugin_before_registration(self, plugin_class: Type[BasePlugin]) -> None:
        """Validate plugin before registration."""
        from ..utils.validation import validate_plugin_structure_shallow

        validation_errors = validate_plugin_structure_shallow(plugin_class)
        if validation_errors:
            raise ValueError(f"Plugin {plugin_class.__name__} failed validation: {validation_errors}")

    def _should_skip_registration(self, plugin_name: str, plugin_class: Type[BasePlugin], plugin_metadata: Any) -> bool:
        """Check if plugin registration should be skipped."""
        if plugin_name not in self._plugins:
            return False

        existing_plugin_class = self._plugin_classes.get(plugin_name)
        if existing_plugin_class is plugin_class:
            self.logger.info(
                f"Plugin '{plugin_name}' already registered with the same class. Skipping duplicate registration."
            )
            return True

        return self._is_duplicate_or_lower_version(plugin_name, existing_plugin_class, plugin_class, plugin_metadata)

    def _is_duplicate_or_lower_version(
        self, plugin_name: str, existing_class: Type[BasePlugin], new_class: Type[BasePlugin], new_metadata: Any
    ) -> bool:
        """Check if new plugin is duplicate or has lower version."""
        existing_metadata = self._plugins[plugin_name].get_metadata()
        existing_version = existing_metadata.version
        new_version = new_metadata.version

        if existing_version == new_version and self._get_plugin_module(existing_class) == self._get_plugin_module(
            new_class
        ):
            self.logger.info(
                f"Plugin '{plugin_name}' v{new_version} from {self._get_plugin_module(new_class)} already registered. Skipping duplicate."
            )
            return True

        return self._is_new_version_lower(existing_version, new_version)

    def _is_new_version_lower(self, existing_version: str, new_version: str) -> bool:
        """Check if new version is lower than existing version."""
        try:
            existing_parsed = Version(str(existing_version))
            new_parsed = Version(str(new_version))
            if new_parsed <= existing_parsed:
                return True
        except Exception:
            if str(new_version) <= str(existing_version):
                return True
        return False

    def _handle_existing_plugin_registration(
        self, plugin_name: str, plugin_class: Type[BasePlugin], plugin_metadata: Any
    ) -> None:
        """Handle case where plugin with same name already exists."""
        existing_class = self._plugin_classes.get(plugin_name)
        existing_metadata = self._plugins[plugin_name].get_metadata()
        existing_version = existing_metadata.version
        new_version = plugin_metadata.version

        self.logger.info(
            f"Plugin '{plugin_name}' already exists: existing v{existing_version} from {self._get_plugin_module(existing_class)}, "
            f"attempting to register v{new_version} from {self._get_plugin_module(plugin_class)}"
        )

        if self._is_new_version_lower(existing_version, new_version):
            existing_module = self._get_plugin_module(existing_class)
            self.logger.info(
                f"Ignoring registration of '{plugin_name}' v{new_version} from {self._get_plugin_module(plugin_class)} "
                f"because existing version v{existing_version} from {existing_module} is higher or equal."
            )
            return

        self.logger.warning(
            f"Plugin '{plugin_name}' is already registered "
            f"(existing: v{existing_version} from {self._get_plugin_module(existing_class)}, new: v{new_version} from {self._get_plugin_module(plugin_class)}). "
            f"Replacing with new version."
        )

    def _complete_plugin_registration(
        self, plugin_name: str, plugin_class: Type[BasePlugin], contract: Any, plugin_metadata: Any
    ) -> None:
        """Complete the plugin registration process."""
        self._plugins[plugin_name] = contract
        self._plugin_classes[plugin_name] = plugin_class
        self.logger.info(f"Registered plugin: {plugin_name} v{plugin_metadata.version}")

    def _get_plugin_module(self, plugin_class: Type[BasePlugin]) -> str:
        """Get the module name for a plugin class."""
        return getattr(plugin_class, "__module__", "unknown")

    def __len__(self) -> int:
        """Return number of registered plugins."""
        return len(self._plugins)

    def __contains__(self, plugin_name: str) -> bool:
        """Return True if a plugin is registered."""
        return plugin_name in self._plugins


_global_registry = PluginRegistry()


def register_plugin(plugin_class: Type[BasePlugin]) -> None:
    """Register a plugin with the global registry."""
    _global_registry.register(plugin_class)


def discover_plugins() -> List[PluginContract]:
    """Return all registered plugin contracts from the global registry."""
    return _global_registry.list_registered_plugins()


def get_plugin_registry() -> PluginRegistry:
    """Return the global plugin registry instance."""
    return _global_registry

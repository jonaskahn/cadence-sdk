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

    def register(self, plugin_class: Type[BasePlugin]) -> None:
        """Register a plugin class.

        Args:
            plugin_class: Class implementing `BasePlugin`.

        Raises:
            ValueError: If registration fails.
        """
        try:
            contract = PluginContract(plugin_class)

            # Lazy import to avoid circular import during module initialization
            from ..utils.validation import validate_plugin_structure_shallow

            errors = validate_plugin_structure_shallow(plugin_class)
            if errors:
                raise ValueError(f"Plugin {plugin_class.__name__} failed validation: {errors}")

            metadata = contract.get_metadata()
            plugin_name = metadata.name

            if plugin_name in self._plugins:
                existing_class = self._plugin_classes.get(plugin_name)
                if existing_class is plugin_class:
                    self.logger.info(
                        f"Plugin '{plugin_name}' already registered with the same class. Skipping duplicate registration."
                    )
                    return

                existing_metadata = self._plugins[plugin_name].get_metadata()
                existing_version = existing_metadata.version
                new_version = metadata.version
                existing_module = getattr(existing_class, "__module__", "unknown")
                new_module = getattr(plugin_class, "__module__", "unknown")

                self.logger.info(
                    f"Plugin '{plugin_name}' already exists: existing v{existing_version} from {existing_module}, "
                    f"attempting to register v{new_version} from {new_module}"
                )

                try:
                    existing_v = Version(str(existing_version))
                    new_v = Version(str(new_version))
                except Exception:
                    existing_v = str(existing_version)
                    new_v = str(new_version)

                if existing_version == new_version and existing_module == new_module:
                    self.logger.info(
                        f"Plugin '{plugin_name}' v{new_version} from {new_module} already registered. Skipping duplicate."
                    )
                    return
                try:
                    if new_v <= existing_v:
                        self.logger.info(
                            f"Ignoring registration of '{plugin_name}' v{new_version} from {new_module} "
                            f"because existing version v{existing_version} from {existing_module} is higher or equal."
                        )
                        return
                except TypeError:
                    if str(new_version) <= str(existing_version):
                        self.logger.info(
                            f"Ignoring registration of '{plugin_name}' v{new_version} from {new_module} "
                            f"because existing version v{existing_version} from {existing_module} is higher or equal."
                        )
                        return
                self.logger.warning(
                    f"Plugin '{plugin_name}' is already registered "
                    f"(existing: v{existing_version} from {existing_module}, new: v{new_version} from {new_module}). "
                    f"Replacing with new version."
                )

            self._plugins[plugin_name] = contract
            self._plugin_classes[plugin_name] = plugin_class

            self.logger.info(f"Registered plugin: {plugin_name} v{metadata.version}")

        except Exception as e:
            self.logger.error(f"Failed to register plugin {plugin_class.__name__}: {e}")
            raise ValueError(f"Plugin registration failed: {e}") from e

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

    def clear_all(self) -> None:
        """Clear the registry."""
        self._plugins.clear()
        self._plugin_classes.clear()
        self.logger.info("Cleared all plugins from registry")

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

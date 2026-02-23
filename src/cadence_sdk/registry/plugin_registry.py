"""Global plugin registry singleton.

This module provides a singleton registry for managing plugin registrations.
Plugins are keyed by their globally unique `pid` (reverse-domain
convention, e.g. "com.example.product_search"), which guarantees that no
two plugins from any source — system, tenant, or environment — can conflict.
"""

import threading
from typing import Dict, List, Optional, Tuple, Type

from packaging import version as pkg_version

from ..base import BasePlugin
from .contracts import PluginContract


class PluginRegistry:
    """Singleton registry for Cadence plugins.

    The PluginRegistry maintains a global registry of all discovered and
    registered plugins, keyed by each plugin's unique `pid`.

    Because plugin IDs use a reverse-domain convention, system plugins
    (e.g., "io.cadence.system.product_search") and tenant plugins
    (e.g., "com.acme.custom_search") occupy separate namespaces and
    can never conflict. The global singleton is therefore safe for
    multi-tenant use.

    Version conflict resolution applies only when the same `pid`
    is discovered from multiple sources (e.g., a pip package and a
    directory scan of the same plugin). In that case, the higher version
    wins.

    This is a singleton class - use PluginRegistry.instance() to access it.

    Thread-safe for concurrent registrations.
    """

    _instance: Optional["PluginRegistry"] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize registry.

        Note: Use PluginRegistry.instance() instead of direct instantiation.
        """
        self._plugins: Dict[str, PluginContract] = {}
        self._versioned_plugins: Dict[Tuple[str, str], PluginContract] = {}
        self._registry_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "PluginRegistry":
        """Get the singleton instance.

        Returns:
            PluginRegistry singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(
        self, plugin_class: Type[BasePlugin], override: bool = False
    ) -> PluginContract:
        """Register a plugin class.

        Args:
            plugin_class: Plugin class to register
            override: If True, override existing registration regardless of version

        Returns:
            PluginContract for the registered plugin

        Raises:
            TypeError: If plugin_class is not a BasePlugin subclass
            ValueError: If plugin with same pid but higher version exists
        """
        if not issubclass(plugin_class, BasePlugin):
            raise TypeError(f"{plugin_class.__name__} must inherit from BasePlugin")

        contract = PluginContract(plugin_class)
        pid = contract.pid

        with self._registry_lock:
            if pid in self._plugins:
                existing_contract = self._plugins[pid]

                if override:
                    self._plugins[pid] = contract
                    self._versioned_plugins[(pid, contract.version)] = contract
                    return contract

                updated_contract = self._resolve_version_conflict(
                    existing_contract, contract
                )
                self._plugins[pid] = updated_contract
            else:
                self._plugins[pid] = contract

            self._versioned_plugins[(pid, contract.version)] = contract
            return self._plugins[pid]

    @staticmethod
    def _resolve_version_conflict(
        existing: PluginContract, new: PluginContract
    ) -> PluginContract:
        """Resolve version conflict between two plugin contracts with the same pid.

        Args:
            existing: Existing plugin contract
            new: New plugin contract

        Returns:
            PluginContract that should be used (higher version preferred)
        """
        try:
            existing_version = pkg_version.parse(existing.version)
            new_version = pkg_version.parse(new.version)

            if new_version >= existing_version:
                return new
            return existing

        except pkg_version.InvalidVersion:
            return new

    def get_plugin(self, pid: str) -> Optional[PluginContract]:
        """Get a registered plugin by pid.

        Args:
            pid: Reverse-domain plugin identifier (e.g., "com.example.search")

        Returns:
            PluginContract if found, None otherwise
        """
        with self._registry_lock:
            return self._plugins.get(pid)

    def get_plugin_by_version(self, pid: str, version: str) -> Optional[PluginContract]:
        """Get a registered plugin by exact pid and version.

        Args:
            pid: Reverse-domain plugin identifier (e.g., "com.example.search")
            version: Exact version string (e.g., "1.2.3")

        Returns:
            PluginContract if found, None otherwise
        """
        with self._registry_lock:
            return self._versioned_plugins.get((pid, version))

    def list_plugin_versions(self, pid: str) -> List[str]:
        """List all registered versions for a given pid.

        Args:
            pid: Reverse-domain plugin identifier

        Returns:
            List of version strings registered for this pid
        """
        with self._registry_lock:
            return [ver for (p, ver) in self._versioned_plugins if p == pid]

    def list_registered_plugins(self) -> List[PluginContract]:
        """List all registered plugins.

        Returns:
            List of all registered PluginContract instances
        """
        with self._registry_lock:
            return list(self._plugins.values())

    def list_plugins_by_capability(self, capability: str) -> List[PluginContract]:
        """List plugins that have a specific capability.

        Args:
            capability: Capability tag to filter by

        Returns:
            List of matching PluginContract instances
        """
        with self._registry_lock:
            return [
                contract
                for contract in self._plugins.values()
                if capability in contract.capabilities
            ]

    def list_plugins_by_type(self, agent_type: str) -> List[PluginContract]:
        """List plugins of a specific agent type.

        Args:
            agent_type: Agent type to filter by

        Returns:
            List of matching PluginContract instances
        """
        with self._registry_lock:
            return [
                contract
                for contract in self._plugins.values()
                if contract.agent_type == agent_type
            ]

    def unregister(self, pid: str) -> bool:
        """Unregister a plugin by pid.

        Args:
            pid: Reverse-domain plugin identifier to unregister

        Returns:
            True if plugin was unregistered, False if not found
        """
        with self._registry_lock:
            if pid in self._plugins:
                del self._plugins[pid]
                return True
            return False

    def clear_all(self) -> None:
        """Clear all registered plugins.

        Warning: This should only be used for testing.
        """
        with self._registry_lock:
            self._plugins.clear()
            self._versioned_plugins.clear()

    def get_all_ids(self) -> List[str]:
        """Get list of all registered plugin IDs.

        Returns:
            List of pid strings
        """
        with self._registry_lock:
            return list(self._plugins.keys())

    def has_plugin(self, pid: str) -> bool:
        """Check if a plugin is registered.

        Args:
            pid: Reverse-domain plugin identifier

        Returns:
            True if plugin is registered
        """
        with self._registry_lock:
            return pid in self._plugins

    def __repr__(self) -> str:
        """String representation."""
        count = len(self._plugins)
        return f"PluginRegistry(plugins={count})"


def register_plugin(
    plugin_class: Type[BasePlugin], override: bool = False
) -> PluginContract:
    """Register a plugin with the global registry.

    This is a convenience function that registers a plugin with the
    singleton PluginRegistry instance. The plugin is keyed by its
    `pid` (reverse-domain, e.g. "com.example.product_search").

    Args:
        plugin_class: Plugin class to register
        override: If True, override existing registration

    Returns:
        PluginContract for the registered plugin

    Example:
        from cadence_sdk import register_plugin, BasePlugin

        class MyPlugin(BasePlugin):
            @staticmethod
            def get_metadata():
                return PluginMetadata(
                    pid="com.example.my_plugin",
                    name="My Plugin",
                    ...
                )

        register_plugin(MyPlugin)
    """
    return PluginRegistry.instance().register(plugin_class, override=override)

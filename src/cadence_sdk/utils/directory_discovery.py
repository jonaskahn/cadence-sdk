"""Directory-based plugin discovery.

This module provides utilities for discovering plugins from filesystem
directories by scanning for Python packages containing plugin.py files.

Supports two directory layouts:

  Flat layout (legacy):
    {dir}/{plugin_name}/plugin.py

  Versioned layout (current):
    {dir}/{pid}/{version}/plugin.py

The scanner detects which layout is present per directory and handles both.
"""

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from ..base import BasePlugin
from ..registry import PluginContract, register_plugin

logger = logging.getLogger(__name__)


class DirectoryPluginDiscovery:
    """Discovers plugins from filesystem directories.

    Scans directories for plugin packages and automatically imports and
    registers them. Handles both the legacy flat layout and the current
    versioned two-level layout ({pid}/{version}/plugin.py).

    All versions found are registered; the PluginRegistry deduplicates by
    keeping the highest version per pid.

    Example:
        discovery = DirectoryPluginDiscovery([
            "/path/to/plugins",
            "/another/path"
        ])

        plugins = discovery.discover()
        print(f"Found {len(plugins)} plugins")
    """

    def __init__(
        self,
        search_paths: Union[str, List[str]],
        auto_register: bool = True,
    ):
        """Initialize discovery scanner.

        Args:
            search_paths: Single path string or list of directory paths to scan
            auto_register: If True, automatically register discovered plugins
        """
        if isinstance(search_paths, str):
            search_paths = [search_paths]
        self.search_paths = [Path(p) for p in search_paths]
        self.auto_register = auto_register
        self._discovered: Dict[str, PluginContract] = {}

    def discover(self) -> List[PluginContract]:
        """Discover all plugins in search paths.

        Returns:
            List of discovered PluginContract instances

        Raises:
            ImportError: If plugin module cannot be imported
        """
        discovered = []

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            if not search_path.is_dir():
                continue

            plugins = self._scan_directory(search_path)
            discovered.extend(plugins)

        self._discovered = {p.name: p for p in discovered}
        return discovered

    def _scan_directory(self, directory: Path) -> List[PluginContract]:
        """Scan a directory for plugin packages.

        Handles two layouts:
          - Flat:      {directory}/{plugin_name}/plugin.py
          - Versioned: {directory}/{pid}/{version}/plugin.py

        A top-level directory item is treated as a pid container (versioned
        layout) when it contains no plugin.py but does contain at least one
        subdirectory. Otherwise, it is treated as the plugin directory itself
        (flat layout).

        Args:
            directory: Directory to scan

        Returns:
            List of discovered plugins (all versions)
        """
        plugins = []

        for item in directory.iterdir():
            if not self._should_scan_item(item):
                continue

            plugin_file = item / "plugin.py"
            if plugin_file.exists():
                contract = self._try_import_and_create_contract(item, plugin_file)
                if contract:
                    plugins.append(contract)
            else:
                plugins.extend(self._discover_from_versioned_pid_dir(item))

        return plugins

    def _discover_from_versioned_pid_dir(self, pid_dir: Path) -> List[PluginContract]:
        """Discover plugins from versioned layout: {pid_dir}/{version}/plugin.py.

        Args:
            pid_dir: Directory containing version subdirectories

        Returns:
            List of discovered PluginContract instances
        """
        plugins = []
        for version_dir in pid_dir.iterdir():
            if not self._should_scan_item(version_dir):
                continue
            versioned_plugin_file = version_dir / "plugin.py"
            if versioned_plugin_file.exists():
                contract = self._try_import_and_create_contract(
                    version_dir, versioned_plugin_file
                )
            else:
                contract = None
                for subdir in version_dir.iterdir():
                    if not self._should_scan_item(subdir):
                        continue

                    nested = subdir / "plugin.py"
                    if not nested.exists():
                        continue

                    contract = self._try_import_and_create_contract(subdir, nested)
                    break
            if contract:
                plugins.append(contract)
        return plugins

    @staticmethod
    def _should_scan_item(item: Path) -> bool:
        """Check if directory item should be scanned for plugins.

        Args:
            item: Path item to check

        Returns:
            True if item should be scanned
        """
        if not item.is_dir():
            return False

        if item.name.startswith(".") or item.name == "__pycache__":
            return False

        return True

    def _try_import_and_create_contract(
        self, package_dir: Path, plugin_file: Path
    ) -> Optional[PluginContract]:
        """Try to import plugin and create contract.

        Args:
            package_dir: Package directory
            plugin_file: Plugin file path

        Returns:
            PluginContract if successful, None otherwise
        """
        try:
            plugin_class = self._import_plugin(package_dir, plugin_file)
            if not plugin_class:
                return None

            if self.auto_register:
                return register_plugin(plugin_class)
            else:
                return PluginContract(plugin_class)

        except Exception as e:
            logger.error(
                "Failed to import plugin from %s: %s", package_dir, e, exc_info=True
            )
            return None

    def _import_plugin(
        self, package_dir: Path, plugin_file: Path
    ) -> Optional[Type[BasePlugin]]:
        """Import plugin.py and extract BasePlugin subclass.

        Args:
            package_dir: Plugin package directory
            plugin_file: Path to plugin.py file

        Returns:
            BasePlugin subclass if found, None otherwise
        """
        module_name = (
            f"_cadence_plugin_{package_dir.name.replace('.', '_').replace('-', '_')}"
        )
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)

        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        plugin_dir = str(package_dir)
        sys.path.insert(0, plugin_dir)

        try:
            spec.loader.exec_module(module)
            return self._find_base_plugin_subclass(module)
        finally:
            if plugin_dir in sys.path:
                sys.path.remove(plugin_dir)

    def _find_base_plugin_subclass(self, module) -> Optional[Type[BasePlugin]]:
        """Find BasePlugin subclass in module.

        Args:
            module: Imported module to search

        Returns:
            BasePlugin subclass if found, None otherwise
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if self._is_plugin_class(attr):
                return attr

        return None

    @staticmethod
    def _is_plugin_class(attr: Any) -> bool:
        """Check if attribute is a valid plugin class.

        Args:
            attr: Attribute to check

        Returns:
            True if attribute is a BasePlugin subclass
        """
        return (
            isinstance(attr, type)
            and issubclass(attr, BasePlugin)
            and attr is not BasePlugin
        )

    def reset(self) -> None:
        """Reset discovery state and re-scan directories."""
        self._discovered.clear()
        self.discover()

    def get_discovered(self) -> Dict[str, PluginContract]:
        """Get dictionary of discovered plugins.

        Returns:
            Dict mapping plugin names to contracts
        """
        return self._discovered.copy()

    def __repr__(self) -> str:
        """String representation."""
        return f"DirectoryPluginDiscovery(paths={len(self.search_paths)}, discovered={len(self._discovered)})"


def discover_plugins(
    search_paths: Union[str, List[str]], auto_register: bool = True
) -> List[PluginContract]:
    """Convenience function to discover plugins from directories.

    Args:
        search_paths: Single path or list of directory paths to scan
        auto_register: If True, register discovered plugins

    Returns:
        List of discovered PluginContract instances

    Example:
        plugins = discover_plugins(["/path/to/plugins"])
        print(f"Discovered: {[p.name for p in plugins]}")
    """
    discovery = DirectoryPluginDiscovery(search_paths, auto_register)
    return discovery.discover()

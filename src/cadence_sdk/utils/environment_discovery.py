"""Environment-installed plugin discovery utilities.

Discovers Cadence SDK plugins that are available in the active Python environment
by scanning all packages and detecting plugin-like structures dynamically.
"""

import importlib.metadata
import importlib.util
import os
from typing import Any, Dict, List, Set

from ..base.loggable import Loggable
from ..registry.plugin_registry import discover_plugins, get_plugin_registry


class PluginDiscoveryManager(Loggable):
    """Manages discovery and import of plugins from the Python environment using generic detection."""

    def __init__(self):
        super().__init__()
        self._imported_packages: Set[str] = set()
        self._plugin_candidates: Dict[str, Dict[str, Any]] = {}

    def reset(self):
        """Reset discovery state."""
        self._imported_packages.clear()
        self._plugin_candidates.clear()

    def import_plugins_from_environment(self, force_reimport: bool = False) -> int:
        """Import all available plugins from the environment using generic detection.

        Args:
            force_reimport: If True, reimport already imported packages

        Returns:
            Number of plugin packages imported
        """
        self.logger.info("Starting generic environment plugin discovery...")

        all_packages = self._get_all_installed_packages()
        self.logger.debug(f"Found {len(all_packages)} total packages to scan")

        imported_count = 0
        for package_name, package_info in all_packages.items():
            if not force_reimport and package_name in self._imported_packages:
                self.logger.debug(f"Package {package_name} already imported, skipping")
                continue

            if self._is_potential_plugin_package(package_name, package_info):
                self.logger.debug(f"Package {package_name} identified as potential plugin")

                if self._try_import_package(package_name):
                    imported_count += 1
                    self.logger.info(f"Successfully imported plugin package: {package_name}")
                else:
                    self.logger.warning(f"Failed to import plugin package: {package_name}")
            else:
                self.logger.debug(f"Package {package_name} not identified as potential plugin - skipping")

        self.logger.info(f"Imported {imported_count} plugin packages")
        return imported_count

    def _get_all_installed_packages(self) -> Dict[str, Dict[str, Any]]:
        """Get all installed packages with their metadata.

        Returns:
            Dictionary mapping package names to their metadata
        """
        packages = {}

        for distribution in importlib.metadata.distributions():
            try:
                name = distribution.metadata["Name"]
                packages[name] = {
                    "distribution": distribution,
                    "version": distribution.metadata.get("Version", "unknown"),
                    "description": distribution.metadata.get("Summary", ""),
                    "requires": distribution.metadata.get_all("Requires-Dist", []),
                    "path": distribution.locate_file("") if hasattr(distribution, "locate_file") else None,
                }
            except Exception as e:
                self.logger.debug(f"Error processing package {distribution.metadata.get('Name', 'unknown')}: {e}")
                continue

        return packages

    def _is_potential_plugin_package(self, package_name: str, package_info: Dict[str, Any]) -> bool:
        """Determine if a package is a potential Cadence plugin using focused detection.

        Args:
            package_name: Name of the package
            package_info: Package metadata and information

        Returns:
            True if the package appears to be a potential Cadence plugin
        """
        # Skip the SDK itself
        if package_name.lower() in ("cadence_sdk", "cadence-sdk"):
            return False

        # Primary: Check if package depends on cadence_sdk (strongest indicator)
        if self._depends_on_cadence_sdk(package_info["distribution"]):
            self.logger.debug(f"Package {package_name} depends on cadence_sdk - importing")
            return True

        # Secondary: Check if package name explicitly suggests it's a Cadence plugin
        if self._name_explicitly_suggests_cadence_plugin(package_name):
            self.logger.debug(f"Package {package_name} name suggests Cadence plugin - importing")
            return True

        # Skip all other packages - too aggressive
        return False

    def _depends_on_cadence_sdk(self, distribution: importlib.metadata.Distribution) -> bool:
        """Check if distribution depends on cadence_sdk.

        Args:
            distribution: Python package distribution to check

        Returns:
            True if the distribution depends on cadence_sdk
        """
        try:
            requires = distribution.metadata.get_all("Requires-Dist")
            if not requires:
                return False

            requirements = [req.split(";")[0].strip().lower() for req in requires]
            return any("cadence_sdk" in req or "cadence-sdk" in req for req in requirements)
        except Exception:
            return False

    def _has_plugin_like_structure(self, package_name: str, package_info: Dict[str, Any]) -> bool:
        """Check if package has a structure that suggests it's a plugin.

        Args:
            package_name: Name of the package
            package_info: Package metadata and information

        Returns:
            True if package structure suggests it's a plugin
        """
        try:
            # Try to import the package to examine its structure
            module_name = package_name.replace("-", "_")
            if not self._module_exists(module_name):
                return False

            module = __import__(module_name, fromlist=[""])

            # Check if it has a __path__ (it's a package)
            if not hasattr(module, "__path__"):
                return False

            # Check if it contains any Python modules that might be plugins
            for path in module.__path__:
                if os.path.exists(path):
                    for item in os.listdir(path):
                        if self._looks_like_plugin_module(item, os.path.join(path, item)):
                            return True

            return False

        except Exception as e:
            self.logger.debug(f"Error checking structure of {package_name}: {e}")
            return False

    def _looks_like_plugin_module(self, name: str, path: str) -> bool:
        """Check if a module/directory looks like it contains a plugin.

        Args:
            name: Name of the item
            path: Path to the item

        Returns:
            True if the item looks like it contains a plugin
        """
        if name.startswith("_") or name in ("__pycache__", "tests", "test", "docs"):
            return False

        if name.endswith(".py"):
            return True

        if os.path.isdir(path) and os.path.exists(os.path.join(path, "__init__.py")):
            return True

        return False

    def _name_suggests_plugin(self, package_name: str) -> bool:
        """Check if package name suggests it's a plugin.

        Args:
            package_name: Name of the package

        Returns:
            True if name suggests it's a plugin
        """
        name_lower = package_name.lower()

        # Common plugin indicators
        plugin_indicators = [
            "plugin",
            "plugins",
            "agent",
            "agents",
            "extension",
            "extensions",
            "module",
            "modules",
            "addon",
            "addons",
            "integration",
            "integrations",
        ]

        return any(indicator in name_lower for indicator in plugin_indicators)

    def _name_suggests_cadence_plugin(self, package_name: str) -> bool:
        """Check if package name suggests it's a Cadence plugin.

        Args:
            package_name: Name of the package

        Returns:
            True if name suggests it's a Cadence plugin
        """
        name_lower = package_name.lower()

        # Cadence-specific plugin indicators
        cadence_indicators = ["cadence", "plugin", "plugins", "agent", "agents"]

        # Must contain at least one Cadence-related term
        return any(indicator in name_lower for indicator in cadence_indicators)

    def _name_explicitly_suggests_cadence_plugin(self, package_name: str) -> bool:
        """Check if package name explicitly suggests it's a Cadence plugin.

        Args:
            package_name: Name of the package

        Returns:
            True if name explicitly suggests it's a Cadence plugin
        """
        name_lower = package_name.lower()

        # Must contain BOTH "cadence" AND plugin-related terms
        has_cadence = "cadence" in name_lower
        has_plugin_terms = any(term in name_lower for term in ["plugin", "plugins", "agent", "agents"])

        return has_cadence and has_plugin_terms

    def _try_import_package(self, package_name: str) -> bool:
        """Try to import a package and scan for plugins.

        Args:
            package_name: Name of the package to import

        Returns:
            True if import was successful
        """
        module_names = self._get_possible_module_names(package_name)

        for module_name in module_names:
            if self._module_exists(module_name):
                try:
                    self.logger.debug(f"Trying to import {package_name} as {module_name}")
                    __import__(module_name)
                    self._imported_packages.add(module_name)
                    self._scan_and_import_plugin_modules(module_name, package_name)
                    return True
                except ImportError as e:
                    self.logger.debug(f"Failed to import {package_name} as {module_name}: {e}")
                except Exception as e:
                    self.logger.warning(f"Unexpected error importing {package_name} as {module_name}: {e}")

        self.logger.warning(f"Could not import package {package_name} with any module name")
        return False

    def _get_possible_module_names(self, package_name: str) -> List[str]:
        """Get possible module names for a package.

        Args:
            package_name: Original package name

        Returns:
            List of possible module names to try
        """
        names = []

        # Original name
        names.append(package_name)

        # Hyphen to underscore conversion
        if "-" in package_name:
            names.append(package_name.replace("-", "_"))

        # Common variations
        if package_name.startswith("cadence-") and package_name.endswith("-plugins"):
            names.append("cadence_plugins")

        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)

        return unique_names

    def _scan_and_import_plugin_modules(self, module_name: str, package_name: str):
        """Scan a package for individual plugin modules and import them.

        Args:
            module_name: Name of the imported module
            package_name: Original package name for logging
        """
        import os

        try:
            module = __import__(module_name, fromlist=[""])
            module_path = getattr(module, "__path__", None)

            if not module_path:
                return

            for path in module_path:
                if os.path.exists(path):
                    self._scan_directory_for_plugins(path, module_name)

        except Exception as e:
            self.logger.debug(f"Error scanning package {module_name} for plugin modules: {e}")

    def _scan_directory_for_plugins(self, directory_path: str, module_name: str):
        """Scan a directory for potential plugin modules.

        Args:
            directory_path: Path to scan
            module_name: Parent module name
        """
        import os

        try:
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)

                if self._is_potential_plugin_module(item, item_path):
                    self._import_plugin_module(item, module_name)

        except Exception as e:
            self.logger.debug(f"Error scanning directory {directory_path}: {e}")

    def _import_plugin_module(self, item_name: str, parent_module: str):
        """Import a single plugin module.

        Args:
            item_name: Name of the item to import
            parent_module: Parent module name
        """
        plugin_module_name = f"{parent_module}.{item_name}"

        if plugin_module_name not in self._imported_packages:
            try:
                __import__(plugin_module_name)
                self._imported_packages.add(plugin_module_name)
                self.logger.debug(f"Imported plugin module: {plugin_module_name}")
            except Exception as e:
                self.logger.debug(f"Failed to import plugin module {item_name}: {e}")

    def _is_potential_plugin_module(self, name: str, path: str) -> bool:
        """Check if a path represents a potential plugin module.

        Args:
            name: Name of the item
            path: Path to the item

        Returns:
            True if the item is a potential plugin module
        """
        import os

        if name.startswith("_") or name.startswith(".") or name in ("__pycache__", "tests", "test"):
            return False

        if name.endswith(".py"):
            return True

        if os.path.isdir(path) and os.path.exists(os.path.join(path, "__init__.py")):
            return True

        return False

    @staticmethod
    def _module_exists(module_name: str) -> bool:
        """Check if a module exists without importing it.

        Args:
            module_name: Name of the module to check

        Returns:
            True if the module exists
        """
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            return False

    def get_installed_environment_packages(self) -> List[str]:
        """Get installed plugin package names from environment.

        Returns:
            List of installed plugin package names
        """
        return [
            name
            for name, info in self._get_all_installed_packages().items()
            if self._is_potential_plugin_package(name, info)
        ]

    def get_imported_environment_packages(self) -> List[str]:
        """Get imported plugin package module names from environment.

        Returns:
            List of imported plugin module names
        """
        return sorted(self._imported_packages)

    def get_registry_summary(self) -> dict:
        """Get summary statistics about the plugin registry.

        Returns:
            Dictionary with registry summary information
        """
        registry = get_plugin_registry()
        plugins = discover_plugins()

        capabilities = self._extract_capabilities(plugins)
        agent_types = self._extract_agent_types(plugins)

        return {
            "total_plugins": len(registry),
            "plugin_names": registry.list_plugin_names(),
            "unique_capabilities": sorted(capabilities),
            "agent_types": sorted(agent_types),
            "installed_packages": self.get_installed_environment_packages(),
            "imported_packages": sorted(self._imported_packages),
        }

    @staticmethod
    def _extract_capabilities(plugins) -> set:
        """Extract unique capabilities from plugins.

        Args:
            plugins: List of plugin objects

        Returns:
            Set of unique capabilities
        """
        capabilities = set()
        for plugin in plugins:
            metadata = plugin.get_metadata()
            capabilities.update(metadata.capabilities)
        return capabilities

    @staticmethod
    def _extract_agent_types(plugins) -> set:
        """Extract unique agent types from plugins.

        Args:
            plugins: List of plugin objects

        Returns:
            Set of unique agent types
        """
        return {plugin.get_metadata().agent_type for plugin in plugins}


_env_discovery = PluginDiscoveryManager()


def import_plugins_from_environment(force_reimport: bool = False) -> int:
    """Import all available plugins from the environment using generic detection.

    Args:
        force_reimport: If True, reimport already imported packages

    Returns:
        Number of plugin packages imported
    """
    return _env_discovery.import_plugins_from_environment(force_reimport)


def reset_environment_discovery():
    """Reset environment discovery state."""
    _env_discovery.reset()


def get_environment_discovery_summary() -> dict:
    """Get discovery and registry summary.

    Returns:
        Dictionary with discovery summary information
    """
    return _env_discovery.get_registry_summary()


def list_installed_environment_packages() -> List[str]:
    """Get installed plugin package names from environment.

    Returns:
        List of installed plugin package names
    """
    return _env_discovery.get_installed_environment_packages()


def list_imported_environment_packages() -> List[str]:
    """Get imported plugin package module names from environment.

    Returns:
        List of imported plugin module names
    """
    return _env_discovery.get_imported_environment_packages()


def reset_environment_discovery_state():
    """Reset environment discovery state."""
    _env_discovery.reset()

"""Discover and import Cadence SDK plugins from directories."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from typing import List, Set

from ..base.loggable import Loggable
from ..registry.plugin_registry import get_plugin_registry


class DirectoryPluginDiscovery(Loggable):
    """Import plugins found in filesystem directories."""

    def __init__(self):
        super().__init__()
        self._loaded_directories: Set[str] = set()
        self._imported_modules: Set[str] = set()

    def reset(self) -> None:
        """Clear cached discovery state."""
        self._loaded_directories.clear()
        self._imported_modules.clear()

    def import_plugins_from_directories(self, directories: List[str], force_reimport: bool = False) -> int:
        """Discover plugins and import their modules.

        Returns:
            int: Number of newly imported modules.
        """
        dirs = self._validate_directories(directories)
        if not dirs:
            self.logger.info("No valid plugin directories provided")
            return 0

        self.logger.info(f"Searching for plugins in directories: {dirs}")
        discovered_count = 0

        for directory in dirs:
            if not force_reimport and directory in self._loaded_directories:
                continue

            try:
                count = self._load_plugins_from_directory(directory)
                discovered_count += count
                self._loaded_directories.add(directory)
            except Exception as e:
                self.logger.error(f"Failed to load plugins from {directory}: {e}")

        return discovered_count

    def _validate_directories(self, directories: List[str]) -> List[str]:
        """Validate and normalize directory paths."""
        validated: List[str] = []
        for directory in directories:
            abs_dir = os.path.abspath(directory)
            if os.path.exists(abs_dir) and os.path.isdir(abs_dir):
                validated.append(abs_dir)
            else:
                self.logger.warning(f"Plugin directory does not exist: {directory}")
        return validated

    def _load_plugins_from_directory(self, directory: str) -> int:
        """Load plugins from a single directory."""
        path = Path(directory)
        loaded_count = 0

        abs_dir = str(path.absolute())
        if abs_dir not in sys.path:
            sys.path.insert(0, abs_dir)

        # Always look for plugin modules in subdirectories
        for item in path.iterdir():
            if self._is_plugin_module(item):
                try:
                    base_name = item.stem if item.is_file() else item.name
                    module_name = base_name

                    if module_name in self._imported_modules:
                        continue

                    if self._import_plugin_module(item, module_name):
                        loaded_count += 1
                        self._imported_modules.add(module_name)
                except Exception as e:
                    self.logger.warning(f"Failed to import plugin from {item}: {e}")

        return loaded_count

    def _is_plugin_module(self, path: Path) -> bool:
        """Check if a path represents a potential plugin module."""
        if path.is_file():
            return path.suffix == ".py" and path.name != "__init__.py" and not path.name.startswith("_")
        if path.is_dir():
            return (path / "__init__.py").exists() and not path.name.startswith("_") and path.name != "__pycache__"
        return False

    def _import_plugin_module(self, path: Path, module_name: str) -> bool:
        """Import a single plugin module."""
        try:
            initial_count = len(get_plugin_registry())

            if path.is_file():
                spec = importlib.util.spec_from_file_location(module_name, path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            else:
                spec = importlib.util.spec_from_file_location(
                    module_name, path / "__init__.py", submodule_search_locations=[str(path)]
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

            final_count = len(get_plugin_registry())
            return final_count > initial_count

        except Exception as e:
            self.logger.warning(f"Failed to import module {module_name} from {path}: {e}")
            return False


_dir_discovery = DirectoryPluginDiscovery()


def import_plugins_from_directories(directories: List[str], force_reimport: bool = False) -> int:
    """Import plugins from directories."""
    return _dir_discovery.import_plugins_from_directories(directories, force_reimport)


def reset_directory_discovery() -> None:
    """Reset directory discovery state."""
    _dir_discovery.reset()


def get_directory_discovery_summary() -> dict:
    """Return summary of directory discovery and registry state."""
    registry = get_plugin_registry()
    return {
        "loaded_directories": sorted(_dir_discovery._loaded_directories),
        "imported_directory_modules": sorted(_dir_discovery._imported_modules),
        "total_plugins": len(registry),
        "plugin_names": registry.list_plugin_names(),
    }


def list_loaded_directories() -> List[str]:
    """Return directories scanned for plugins."""
    return sorted(_dir_discovery._loaded_directories)


def list_imported_directory_modules() -> List[str]:
    """Return plugin modules imported from directories."""
    return sorted(_dir_discovery._imported_modules)

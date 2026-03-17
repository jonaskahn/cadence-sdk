"""Base plugin interface for Cadence SDK.

This module defines the BasePlugin abstract class that all plugins
must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .agent import BaseAgent
from .metadata import PluginMetadata


class BasePlugin(ABC):
    """Abstract base class for Cadence plugins.

    All plugins must inherit from this class and implement the required
    static methods. A plugin is a factory for creating agent instances.

    The plugin class itself should be stateless - all state belongs to
    the agent instances it creates.

    Required Methods (static):
        - get_metadata(): Return PluginMetadata describing the plugin
        - create_agent(): Return a BaseAgent instance

    Optional Methods:
        - get_settings_schema(): Return settings schema (alternative to @plugin_settings)
        - validate_dependencies(): Check if dependencies are available
        - health_check(): Return health status information

    Example:
        class MyPlugin(BasePlugin):
            @staticmethod
            def get_metadata() -> PluginMetadata:
                return PluginMetadata(
                    name="my_plugin",
                    version="1.0.0",
                    description="My awesome plugin",
                    capabilities=["search"]
                )

            @staticmethod
            def create_agent() -> BaseAgent:
                return MyAgent()

            @staticmethod
            def validate_dependencies() -> List[str]:
                errors = []
                try:
                    import required_package
                except ImportError:
                    errors.append("required_package not found")
                return errors
    """

    @staticmethod
    @abstractmethod
    def get_metadata() -> PluginMetadata:
        """Return PluginMetadata describing the plugin's name, version, capabilities, and requirements."""
        ...

    @staticmethod
    @abstractmethod
    def create_agent() -> BaseAgent:
        """Return a new BaseAgent instance. Each call should return a fresh instance."""
        ...

    @staticmethod
    def validate_dependencies() -> List[str]:
        """Return a list of error messages if dependencies are missing, or empty list if OK."""
        return []

    @staticmethod
    def get_settings_schema() -> List[Dict[str, Any]] | None:
        """Return list of setting definitions, or empty list. Alternative to @plugin_settings."""
        return []

    @staticmethod
    def health_check() -> Dict[str, Any]:
        """Return a dictionary with health status information."""
        return {"status": "unknown"}

    def __repr__(self) -> str:
        try:
            metadata = self.get_metadata()
            return f"{self.__class__.__name__}(name='{metadata.name}', version='{metadata.version}')"
        except Exception:
            return f"{self.__class__.__name__}()"

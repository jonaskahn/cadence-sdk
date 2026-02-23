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
        """Get plugin metadata.

        This static method must return a PluginMetadata instance describing
        the plugin's name, version, capabilities, and requirements.

        Returns:
            PluginMetadata instance

        Example:
            @staticmethod
            def get_metadata() -> PluginMetadata:
                return PluginMetadata(
                    name="web_search",
                    version="1.0.0",
                    description="Web search using DuckDuckGo",
                    capabilities=["search", "web"],
                    dependencies=["duckduckgo-search>=3.0"],
                )
        """
        pass

    @staticmethod
    @abstractmethod
    def create_agent() -> BaseAgent:
        """Create an agent instance.

        This static method must return a new BaseAgent instance.
        Each call should return a fresh instance.

        Returns:
            BaseAgent instance

        Example:
            @staticmethod
            def create_agent() -> BaseAgent:
                return WebSearchAgent()
        """
        pass

    @staticmethod
    def validate_dependencies() -> List[str]:
        """Validate plugin dependencies (optional).

        This optional method checks if all required dependencies are available
        and properly configured. Return a list of error messages, or an empty
        list if everything is OK.

        Returns:
            List of error messages (empty if OK)

        Example:
            @staticmethod
            def validate_dependencies() -> List[str]:
                errors = []

                # Check for required package
                try:
                    import duckduckgo_search
                except ImportError:
                    errors.append("duckduckgo-search package not installed")

                # Check for environment variable
                import os
                if not os.getenv("API_KEY"):
                    errors.append("API_KEY environment variable not set")

                return errors
        """
        return []

    @staticmethod
    def health_check() -> Dict[str, Any]:
        """Perform health check (optional).

        This optional method can verify that the plugin is working correctly.
        Return a dictionary with health status information.

        Returns:
            Dictionary with health information

        Example:
            @staticmethod
            def health_check() -> Dict[str, Any]:
                return {
                    "status": "healthy",
                    "checks": {
                        "api_accessible": True,
                        "rate_limit_ok": True,
                    },
                    "timestamp": time.time(),
                }
        """
        return {"status": "unknown"}

    def __repr__(self) -> str:
        """String representation of plugin."""
        try:
            metadata = self.get_metadata()
            return f"{self.__class__.__name__}(name='{metadata.name}', version='{metadata.version}')"
        except Exception:
            return f"{self.__class__.__name__}()"

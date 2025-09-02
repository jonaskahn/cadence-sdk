"""Base plugin interface for Cadence plugins."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .agent import BaseAgent
from .metadata import PluginMetadata


class BasePlugin(ABC):
    """Base interface that all Cadence plugins must implement.

    Each plugin must:
    1. Implement get_metadata() to declare its capabilities
    2. Implement create_agent() to provide an agent instance
    3. Optionally implement validation and configuration methods
    """

    @staticmethod
    @abstractmethod
    def get_metadata() -> PluginMetadata:
        """Return plugin metadata used for discovery and routing.

        Returns:
            PluginMetadata: Complete plugin metadata
        """
        pass

    @staticmethod
    @abstractmethod
    def create_agent() -> BaseAgent:
        """Create and return the plugin agent instance.

        Returns:
            BaseAgent: Configured agent instance
        """
        pass

    @staticmethod
    def validate_dependencies() -> List[str]:
        """Validate plugin dependencies.

        Override this method to check if required dependencies are available,
        API keys are configured, external services are accessible, etc.

        Returns:
            List[str]: List of error messages; empty if all checks pass
        """
        return []

    @staticmethod
    def health_check() -> Dict[str, Any]:
        """Perform plugin health check.

        Override this method to implement custom health checks for your plugin.
        This might include checking API connectivity, database connections, etc.

        Returns:
            Dict[str, Any]: Health status with 'healthy' boolean and optional details
        """
        return {"healthy": True, "details": "No custom health checks implemented"}

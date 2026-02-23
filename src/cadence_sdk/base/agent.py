"""Base agent interface for Cadence SDK.

This module defines the BaseAgent abstract class that all plugin agents
must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAgent(ABC):
    """Abstract base class for Cadence agents.

    All plugin agents must inherit from this class and implement
    the required abstract methods.

    A BaseAgent represents a specialized AI agent that provides specific
    tools and capabilities. The framework handles LLM configuration,
    orchestration, and all continue/stop routing decisions; the agent
    focuses solely on tools and domain logic.

    Required Methods:
        - get_tools(): Return list of UvTool instances
        - get_system_prompt(): Return system prompt for this agent

    Optional Methods:
        - initialize(config): Called once when agent is created
        - cleanup(): Called when agent is being destroyed
    """

    @abstractmethod
    def get_tools(self) -> List["UvTool"]:  # type: ignore[name-defined]  # noqa: F821
        """Get list of tools provided by this agent.

        Returns:
            List of UvTool instances

        Example:
            def get_tools(self) -> List[UvTool]:
                return [
                    self.search_tool,
                    self.summarize_tool,
                ]
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get system prompt for this agent.

        The system prompt should describe:
        - What this agent does
        - When to use its tools
        - Any important guidelines or constraints

        The framework may prepend state information and append routing
        guidance. The prompt can be overridden per orchestrator instance
        via Tier 4 node_settings.plugins.{pid}.system_prompt.

        Returns:
            System prompt string

        Example:
            def get_system_prompt(self) -> str:
                return '''You are a web search specialist.
                Use the search tool to find information on the internet.
                Always cite sources in your responses.'''
        """
        pass

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize agent with configuration.

        This optional method is called once when the agent is first created.
        Use it to set up any required state, connections, or resources.

        Args:
            config: Configuration dictionary (from settings resolver)

        Example:
            def initialize(self, config: Dict[str, Any]) -> None:
                self.api_key = config.get("api_key")
                self.max_results = config.get("max_results", 10)
        """
        pass

    async def cleanup(self) -> None:
        """Clean up agent resources.

        This optional method is called when the agent is being destroyed.
        Use it to close connections, release resources, etc.

        Example:
            async def cleanup(self) -> None:
                if hasattr(self, 'http_client'):
                    await self.http_client.close()
        """
        pass

    def get_settings_schema(self) -> List[Dict[str, Any]]:
        """Get settings schema for this agent (optional).

        Alternative to @plugin_settings decorator. Define configuration
        requirements programmatically.

        Returns:
            List of setting definitions

        Example:
            def get_settings_schema(self) -> List[Dict[str, Any]]:
                return [
                    {
                        "key": "api_key",
                        "type": "str",
                        "required": True,
                        "sensitive": True,
                        "description": "API key for service"
                    },
                    {
                        "key": "max_results",
                        "type": "int",
                        "default": 10,
                        "description": "Maximum number of results"
                    }
                ]
        """
        return []

    def __repr__(self) -> str:
        """String representation of agent."""
        return f"{self.__class__.__name__}()"

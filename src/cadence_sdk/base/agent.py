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
        ...

    def initialize(self, config: Dict[str, Any]) -> None:
        """Optional — override to set up state when the agent is first created.

        Args:
            config: Configuration dictionary (from settings resolver)
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class BaseSpecializedAgent(BaseAgent, ABC):
    """Base class for tool-focused agents in multi-agent orchestration modes.

    Specialized agents expose tools and a system prompt describing their
    capabilities to the orchestrator's router and planner.
    They do NOT support grounded mode — use BaseScopedAgent for that.
    """

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Describe this agent's tools and guidelines for the orchestrator."""
        ...


class BaseScopedAgent(BaseAgent, ABC):
    """Base class for context-anchored agents designed for grounded mode.

    Scoped agents are embedded in a specific context (a product page, a document,
    a record). They support grounded mode by implementing load_anchor
    (to load the anchor record) and build_scope_rules (to define scope rules).

    A scoped agent CAN also extend BaseSpecializedAgent to support both modes.
    """

    @abstractmethod
    async def load_anchor(self, resource_id: str) -> Dict[str, Any]:
        """Fetch the primary context for a given resource identifier (URL, ID, slug).

        Called once on the first conversation turn when resource_id is provided.
        The returned dict is injected into the grounded agent's system prompt.

        Args:
            resource_id: A URL, database record ID, slug, or any unique identifier
                         pointing to the resource this conversation is anchored to.

        Returns:
            Dict with the resource's full details. Return {} if not found.
        """
        ...

    @abstractmethod
    def build_scope_rules(self, context: Dict[str, Any]) -> str:
        """Generate a scope instruction from the fetched primary context.

        Called by the grounded orchestrator when no static scope_instruction
        is configured. The returned string tells the scope guard what is in
        and out of bounds for this conversation.

        Args:
            context: The dict returned by load_anchor.

        Returns:
            A human-readable scope description string.
        """
        ...

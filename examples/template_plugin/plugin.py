"""Template plugin demonstrating Cadence SDK usage.

This is a complete example plugin that demonstrates:
- Plugin and agent structure
- Tool declaration using @uvtool
- Settings schema declaration using @plugin_settings
- Sync and async tools
- State management
"""

from typing import List

from cadence_sdk import (
    BaseAgent,
    BasePlugin,
    CacheConfig,
    PluginMetadata,
    UvTool,
    plugin_settings,
    uvtool,
)


def _simulate_search_results(query: str, max_results: int) -> str:
    """Simulate search API response (placeholder for real implementation)."""
    return f"Search results for '{query}' (max: {max_results} results)"


async def _simulate_async_fetch(url: str) -> str:
    """Simulate async fetch (placeholder for aiohttp or similar)."""
    return f"Data fetched from {url}"


class TemplateAgent(BaseAgent):
    """Example agent with basic tools."""

    def __init__(self):
        """Initialize agent with tools as instance attributes."""
        self.greeting = "Hello"
        self.max_results = 10

        self._greet_tool = self._create_greet_tool()
        self._search_tool = self._create_search_tool()
        self._fetch_tool = self._create_fetch_tool()

    def initialize(self, config: dict) -> None:
        """Initialize with configuration.

        Args:
            config: Configuration dict from settings resolver
        """
        self.greeting = config.get("greeting", "Hello")
        self.max_results = config.get("max_results", 10)
        self.enable_cache = config.get("enable_cache", True)

    def _create_greet_tool(self) -> UvTool:
        """Create greet tool."""

        @uvtool
        def greet(name: str) -> str:
            """Greet a user by name.

            Args:
                name: Name of the person to greet

            Returns:
                Greeting message
            """
            return f"{self.greeting}, {name}!"

        return greet

    def _create_search_tool(self) -> UvTool:
        """Create search tool with caching."""

        @uvtool(cache=CacheConfig(ttl=3600, similarity_threshold=0.7))
        def search(query: str) -> str:
            """Search for information.

            This is a cached tool - similar queries will return cached results.
            Caching enabled with 1 hour TTL and 0.7 similarity threshold.

            Args:
                query: Search query

            Returns:
                Search results
            """
            return _simulate_search_results(query, self.max_results)

        return search

    def _create_fetch_tool(self) -> UvTool:
        """Create async fetch tool."""

        @uvtool
        async def async_fetch(url: str) -> str:
            """Asynchronously fetch data from a URL.

            This demonstrates an async tool.

            Args:
                url: URL to fetch

            Returns:
                Fetched data (simulated)
            """
            return await _simulate_async_fetch(url)

        return async_fetch

    def get_tools(self) -> List[UvTool]:
        """Get list of tools provided by this agent.

        Returns:
            List of UvTool instances
        """
        return [
            self._greet_tool,
            self._search_tool,
            self._fetch_tool,
        ]

    def get_system_prompt(self) -> str:
        """Get system prompt for this agent.

        Returns:
            System prompt string
        """
        return """You are a helpful template agent demonstrating Cadence SDK capabilities.

You have access to the following tools:
- greet: Greet users by name
- search: Search for information (cached)
- async_fetch: Asynchronously fetch data from URLs

Use these tools to help users with their requests."""

    async def cleanup(self) -> None:
        """Clean up resources (e.g. close connections)."""
        pass


@plugin_settings(
    [
        {
            "key": "greeting",
            "name": "Greeting",
            "type": "str",
            "default": "Hello",
            "description": "Greeting message to use",
            "required": False,
        },
        {
            "key": "max_results",
            "name": "Max Results",
            "type": "int",
            "default": 10,
            "description": "Maximum number of search results",
            "required": False,
        },
        {
            "key": "enable_cache",
            "name": "Enable Cache",
            "type": "bool",
            "default": True,
            "description": "Enable result caching",
            "required": False,
        },
        {
            "key": "api_key",
            "name": "API Key",
            "type": "str",
            "required": True,
            "sensitive": True,
            "description": "API key for external service (example of required sensitive setting)",
        },
    ]
)
class TemplatePlugin(BasePlugin):
    """Template plugin for demonstration."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        """Get plugin metadata.

        Returns:
            PluginMetadata instance
        """
        return PluginMetadata(
            pid="io.cadence.examples.template_plugin",
            name="Template Plugin",
            version="1.0.0",
            description="Template plugin demonstrating Cadence SDK features",
            capabilities=["greeting", "search", "fetch"],
            dependencies=[],
            agent_type="specialized",
            stateless=True,
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        """Create agent instance.

        Returns:
            TemplateAgent instance
        """
        return TemplateAgent()

    @staticmethod
    def validate_dependencies() -> List[str]:
        """Validate dependencies. Template has no external deps, always valid."""
        return []

    @staticmethod
    def health_check() -> dict:
        """Perform health check.

        Returns:
            Health status dict
        """
        return {
            "status": "healthy",
            "message": "Template plugin is operational",
        }

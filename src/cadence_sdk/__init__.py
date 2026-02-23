"""Cadence SDK - Framework-agnostic plugin development kit.

This SDK provides a unified interface for building AI agent plugins that
work across multiple orchestration frameworks (LangGraph, OpenAI Agents, Google ADK).

Key Concepts:
    - **Plugins**: Factory classes that create agent instances
    - **Agents**: Specialized AI agents that provide tools and capabilities
    - **Tools**: Functions that agents can invoke (@uvtool decorator)
    - **State**: Unified state management across frameworks (UvState)
    - **Messages**: Framework-agnostic message types (UvMessage, etc.)

Example:
    from cadence_sdk import (
        BasePlugin, BaseAgent, PluginMetadata,
        uvtool, UvTool, UvHumanMessage, register_plugin
    )

    class MyAgent(BaseAgent):
        @uvtool
        def search(self, query: str) -> str:
            '''Search for information.'''
            return f"Results for: {query}"

        def get_tools(self):
            return [self.search]

        def get_system_prompt(self):
            return "You are a helpful search assistant."

    class MyPlugin(BasePlugin):
        @staticmethod
        def get_metadata():
            return PluginMetadata(
                pid="com.example.my_plugin",
                name="My Plugin",
                version="1.0.0",
                description="A search plugin"
            )

        @staticmethod
        def create_agent():
            return MyAgent()

    register_plugin(MyPlugin)

Version: 2.0.1
"""

__version__ = "2.0.1"

# Base interfaces
from .base import BaseAgent, BasePlugin, Loggable, PluginMetadata

# Decorators
from .decorators import plugin_settings

# Registry
from .registry import PluginContract, PluginRegistry, register_plugin

# Type system
from .types import CacheConfig  # Messages; Tools; State
from .types import (
    AgentStateFields,
    PluginContext,
    PluginContextFields,
    RoutingHelpers,
    StateHelpers,
    ToolCall,
    UvAIMessage,
    UvHumanMessage,
    UvMessage,
    UvState,
    UvSystemMessage,
    UvTool,
    UvToolMessage,
    create_initial_state,
    merge_messages,
    uvtool,
)

# Utilities
from .utils import (
    DirectoryPluginDiscovery,
    check_dependency_installed,
    discover_plugins,
    install_dependencies,
    validate_plugin_structure,
    validate_plugin_structure_shallow,
)

# Public API
__all__ = [
    # Version
    "__version__",
    # Base interfaces
    "PluginMetadata",
    "BaseAgent",
    "BasePlugin",
    "Loggable",
    # Messages
    "UvMessage",
    "UvHumanMessage",
    "UvAIMessage",
    "UvSystemMessage",
    "UvToolMessage",
    "ToolCall",
    # Tools
    "UvTool",
    "uvtool",
    "CacheConfig",
    # State
    "UvState",
    "PluginContext",
    "AgentStateFields",
    "PluginContextFields",
    "StateHelpers",
    "RoutingHelpers",
    "merge_messages",
    "create_initial_state",
    # Registry
    "PluginContract",
    "PluginRegistry",
    "register_plugin",
    # Utilities
    "validate_plugin_structure_shallow",
    "validate_plugin_structure",
    "DirectoryPluginDiscovery",
    "discover_plugins",
    "install_dependencies",
    "check_dependency_installed",
    # Decorators
    "plugin_settings",
]

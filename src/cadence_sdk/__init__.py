"""Cadence SDK - Plugin Development Framework for Cadence AI.

Provides the core SDK for building custom AI agent plugins for the Cadence multi-agent AI framework.
Includes base classes, utilities, and tools for creating extensible agent systems.

Key Components:
    - BaseAgent: Base class for custom AI agents
    - BasePlugin: Base class for plugin management
    - PluginMetadata: Plugin configuration and metadata
    - Tool: Base class for agent tools
    - Registry: Plugin registration system
"""

from cadence_sdk.base.agent import BaseAgent
from cadence_sdk.base.metadata import ModelConfig, PluginMetadata
from cadence_sdk.base.plugin import BasePlugin
from cadence_sdk.registry.plugin_registry import PluginRegistry, discover_plugins, get_plugin_registry, register_plugin
from cadence_sdk.tools.decorators import tool
from cadence_sdk.tools.registry import ToolRegistry

__version__ = "1.0.6"
__all__ = [
    "BaseAgent",
    "BasePlugin",
    "PluginMetadata",
    "ModelConfig",
    "PluginRegistry",
    "ToolRegistry",
    "tool",
    "discover_plugins",
    "register_plugin",
    "get_plugin_registry",
]

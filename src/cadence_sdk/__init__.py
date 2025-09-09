"""Cadence SDK - Plugin Development Framework for Cadence AI"""

from .base.agent import BaseAgent
from .base.metadata import ModelConfig, PluginMetadata
from .base.plugin import BasePlugin
from .decorators.tool import tool
from .registry.plugin_registry import PluginRegistry, discover_plugins, get_plugin_registry, register_plugin
from .types.state import AgentState, PluginContext, RoutingHelpers, StateHelpers, StateValidation

__version__ = "1.3.0"
__all__ = [
    "BaseAgent",
    "BasePlugin",
    "PluginMetadata",
    "ModelConfig",
    "PluginRegistry",
    "tool",
    "discover_plugins",
    "register_plugin",
    "get_plugin_registry",
    "AgentState",
    "PluginContext",
    "StateHelpers",
    "RoutingHelpers",
    "StateValidation",
]

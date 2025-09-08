"""Cadence SDK - Plugin Development Framework for Cadence AI"""

from cadence_sdk.base.agent import BaseAgent
from cadence_sdk.base.metadata import ModelConfig, PluginMetadata
from cadence_sdk.base.plugin import BasePlugin
from cadence_sdk.registry.plugin_registry import PluginRegistry, discover_plugins, get_plugin_registry, register_plugin
from cadence_sdk.tools.decorators import tool
from cadence_sdk.types.state import AgentState, PluginContext, RoutingHelpers, StateHelpers, StateValidation

__version__ = "1.1.0"
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

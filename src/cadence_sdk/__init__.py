__version__ = "2.0.8"

from .base import BaseAgent, BasePlugin, Loggable, PluginMetadata
from .decorators import plugin_settings
from .registry import PluginContract, PluginRegistry, register_plugin
from .types import (
    StreamFilter,
    ToolCall,
    UvAIMessage,
    UvHumanMessage,
    UvMessage,
    UvState,
    UvSystemMessage,
    UvTool,
    UvToolMessage,
    uvtool,
)
from .utils import (
    DirectoryPluginDiscovery,
    build_plugin_zip,
    check_dependency_installed,
    discover_plugins,
    install_dependencies,
    validate_plugin_structure,
    validate_plugin_structure_shallow,
)

__all__ = [
    "__version__",
    "PluginMetadata",
    "BaseAgent",
    "BasePlugin",
    "Loggable",
    "UvMessage",
    "UvHumanMessage",
    "UvAIMessage",
    "UvSystemMessage",
    "UvToolMessage",
    "ToolCall",
    "UvTool",
    "uvtool",
    "StreamFilter",
    "UvState",
    "PluginContract",
    "PluginRegistry",
    "register_plugin",
    "validate_plugin_structure_shallow",
    "validate_plugin_structure",
    "DirectoryPluginDiscovery",
    "discover_plugins",
    "install_dependencies",
    "check_dependency_installed",
    "build_plugin_zip",
    "plugin_settings",
]

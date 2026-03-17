__version__ = "2.0.10"

from .base import (
    BaseAgent,
    BasePlugin,
    BaseScopedAgent,
    BaseSpecializedAgent,
    Loggable,
    PluginMetadata,
)
from .exceptions import CadenceException
from .decorators import plugin_settings
from .registry import PluginContract, PluginRegistry, register_plugin
from .types import (
    StreamFilter,
    ToolCall,
    UvAIMessage,
    UvContextMessage,
    UvHumanMessage,
    UvMessage,
    UvState,
    UvSystemMessage,
    UvTool,
    UvToolMessage,
    uvtool,
)
from .utils import (
    check_dependency_installed,
    install_dependencies,
    validate_plugin_structure,
    validate_plugin_structure_shallow,
)

__all__ = [
    "__version__",
    "CadenceException",
    "PluginMetadata",
    "BaseAgent",
    "BasePlugin",
    "BaseScopedAgent",
    "BaseSpecializedAgent",
    "Loggable",
    "UvMessage",
    "UvHumanMessage",
    "UvAIMessage",
    "UvSystemMessage",
    "UvToolMessage",
    "UvContextMessage",
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
    "install_dependencies",
    "check_dependency_installed",
    "plugin_settings",
]

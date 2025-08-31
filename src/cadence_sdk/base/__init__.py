"""Base interfaces and types for Cadence plugins."""

from .agent import BaseAgent
from .metadata import ModelConfig, PluginMetadata
from .plugin import BasePlugin

__all__ = ["BaseAgent", "PluginMetadata", "ModelConfig", "BasePlugin"]

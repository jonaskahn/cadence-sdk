"""Base classes and interfaces for Cadence SDK plugins."""

from .agent import BaseAgent
from .loggable import Loggable
from .metadata import PluginMetadata
from .plugin import BasePlugin

__all__ = [
    "PluginMetadata",
    "BaseAgent",
    "BasePlugin",
    "Loggable",
]

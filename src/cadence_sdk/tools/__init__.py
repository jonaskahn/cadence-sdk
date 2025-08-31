"""Tool utilities for Cadence plugins."""

from langchain_core.tools import Tool

from .decorators import tool
from .registry import ToolRegistry

type AgentTool = Tool

__all__ = ["Tool", "tool", "ToolRegistry"]

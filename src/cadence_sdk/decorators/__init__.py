"""Tool utilities for Cadence plugins.

Re-exports LangChain tool types and provides tool registration functionality.
"""

from langchain_core.tools import Tool

from .schema import list_schema, object_schema
from .tool import tool

type AgentTool = Tool

__all__ = ["Tool", "tool", "object_schema", "list_schema"]

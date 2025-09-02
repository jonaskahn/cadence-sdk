"""Tool decorators for Cadence plugins.

Re-exports the LangChain tool decorator for use in Cadence plugins.
This provides a simple way to create and register tools with the @tool decorator.
"""

from langchain_core.tools import tool as langchain_tool

tool = langchain_tool

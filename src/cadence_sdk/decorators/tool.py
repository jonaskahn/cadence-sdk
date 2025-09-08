"""Tool tools for Cadence plugins.

Re-exports the LangChain tool tools for use in Cadence plugins.
This provides a simple way to create and register tools with the @tool tools.
"""

from langchain_core.tools import tool as langchain_tool

tool = langchain_tool

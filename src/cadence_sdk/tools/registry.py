"""Tool registry for managing plugin tools."""

from typing import Dict, List, Set

from langchain_core.tools import Tool


class ToolRegistry:
    """Registry for managing tools across plugins.

    Provides functionality to:
    - Discover all available tools
    - Group tools by plugin
    - Detect tool name conflicts
    - Provide tool metadata
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._plugin_tools: Dict[str, List[str]] = {}

    def register_tool(self, tool: Tool, plugin_name: str) -> None:
        """Register a tool from a specific plugin.

        Args:
            tool: The tool to register
            plugin_name: Name of the plugin providing this tool

        Raises:
            ValueError: If tool name conflicts with existing tool
        """
        if tool.name in self._tools:
            existing_plugin = self._get_plugin_for_tool(tool.name)
            if existing_plugin != plugin_name:
                raise ValueError(
                    f"Tool name conflict: '{tool.name}' is already registered " f"by plugin '{existing_plugin}'"
                )

        self._tools[tool.name] = tool
        if plugin_name not in self._plugin_tools:
            self._plugin_tools[plugin_name] = []
        if tool.name not in self._plugin_tools[plugin_name]:
            self._plugin_tools[plugin_name].append(tool.name)

    def register_plugin_tools(self, tools: List[Tool], plugin_name: str) -> None:
        """Register all tools from a plugin.

        Args:
            tools: List of tools to register
            plugin_name: Name of the plugin providing these tools
        """
        for tool in tools:
            self.register_tool(tool, plugin_name)

    def get_tool(self, name: str) -> Tool:
        """Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool: The requested tool

        Raises:
            KeyError: If tool is not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self._tools[name]

    def get_plugin_tools(self, plugin_name: str) -> List[Tool]:
        """Get all tools for a specific plugin.

        Args:
            plugin_name: Name of the plugin

        Returns:
            List[Tool]: Tools provided by the plugin
        """
        if plugin_name not in self._plugin_tools:
            return []

        return [self._tools[tool_name] for tool_name in self._plugin_tools[plugin_name]]

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools.

        Returns:
            List[Tool]: All registered tools
        """
        return list(self._tools.values())

    def get_tool_names(self) -> Set[str]:
        """Get names of all registered tools.

        Returns:
            Set[str]: Set of tool names
        """
        return set(self._tools.keys())

    def get_plugin_names(self) -> Set[str]:
        """Get names of all plugins with registered tools.

        Returns:
            Set[str]: Set of plugin names
        """
        return set(self._plugin_tools.keys())

    def _get_plugin_for_tool(self, tool_name: str) -> str:
        """Get the plugin name that provides a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            str: Plugin name that provides the tool

        Raises:
            KeyError: If tool is not found
        """
        for plugin_name, tool_names in self._plugin_tools.items():
            if tool_name in tool_names:
                return plugin_name
        raise KeyError(f"Tool '{tool_name}' not found in any plugin")

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        self._plugin_tools.clear()

    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister all tools from a plugin.

        Args:
            plugin_name: Name of the plugin to unregister
        """
        if plugin_name not in self._plugin_tools:
            return

        tool_names = self._plugin_tools[plugin_name]
        for tool_name in tool_names:
            if tool_name in self._tools:
                del self._tools[tool_name]

        del self._plugin_tools[plugin_name]

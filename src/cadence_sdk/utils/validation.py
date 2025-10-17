"""Validation utilities for Cadence plugins."""

import inspect
from typing import Any, List, Type

from langchain_core.tools import BaseTool

from ..base.agent import BaseAgent
from ..base.metadata import PluginMetadata
from ..base.plugin import BasePlugin


def _is_valid_version_format(version: str) -> bool:
    """Check if version string follows semantic versioning format."""
    if not version or len(version.split(".")) < 2:
        return False

    return all(part.isdigit() for part in version.split("."))


def _validate_required_methods(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate that required methods exist and are callable."""
    errors = []
    required_methods = ["get_metadata", "create_agent"]

    for method_name in required_methods:
        if not _method_exists_and_callable(plugin_class, method_name):
            errors.append(f"Plugin must implement {method_name}() method")

    return errors


def _method_exists_and_callable(obj: Any, method_name: str) -> bool:
    """Check if an object has a callable method."""
    return hasattr(obj, method_name) and callable(getattr(obj, method_name))


def _validate_single_tool(tool: BaseTool, index: int) -> List[str]:
    """Validate a single tool."""
    errors = []

    if not _has_valid_name(tool):
        errors.append(f"Tool {index} must have a name")

    if not _has_valid_description(tool):
        errors.append(f"Tool {index} must have a description")

    if not _has_callable_function(tool):
        errors.append(f"Tool {index} must have a callable func attribute")

    return errors


def _has_valid_name(tool: BaseTool) -> bool:
    """Check if tool has a valid name."""
    return bool(tool.name and tool.name.strip())


def _has_valid_description(tool: BaseTool) -> bool:
    """Check if tool has a valid description."""
    return bool(tool.description and tool.description.strip())


def _has_callable_function(tool: BaseTool) -> bool:
    """Check if tool has a callable function (sync or async)."""
    if hasattr(tool, "func") and callable(getattr(tool, "func")):
        return True

    if hasattr(tool, "coroutine") and callable(getattr(tool, "coroutine")):
        return True

    return False


def validate_metadata(metadata: PluginMetadata) -> List[str]:
    """Validate plugin metadata."""
    errors = []

    if not _has_valid_plugin_name(metadata):
        errors.append("Plugin name cannot be empty")

    if not _has_valid_version(metadata):
        errors.append("Plugin version cannot be empty")

    if not _has_valid_description(metadata):
        errors.append("Plugin description cannot be empty")

    if not _has_capabilities(metadata):
        errors.append("Plugin must define at least one capability")

    if not _has_valid_agent_type(metadata):
        valid_types = {"specialized", "general", "utility"}
        errors.append(f"Invalid agent_type: {metadata.agent_type}. Must be one of {valid_types}")

    if not _is_valid_version_format(metadata.version):
        errors.append(f"Invalid version format: {metadata.version}")

    return errors


def _has_valid_plugin_name(metadata: PluginMetadata) -> bool:
    """Check if plugin has a valid name."""
    return bool(metadata.name and metadata.name.strip())


def _has_valid_version(metadata: PluginMetadata) -> bool:
    """Check if plugin has a valid version."""
    return bool(metadata.version and metadata.version.strip())


def _has_valid_description(metadata: PluginMetadata) -> bool:
    """Check if plugin has a valid description."""
    return bool(metadata.description and metadata.description.strip())


def _has_capabilities(metadata: PluginMetadata) -> bool:
    """Check if plugin has capabilities defined."""
    return bool(metadata.capabilities)


def _has_valid_agent_type(metadata: PluginMetadata) -> bool:
    """Check if plugin has a valid agent type."""
    valid_types = {"specialized", "general", "utility"}
    return metadata.agent_type in valid_types


def validate_tools(tools: List[BaseTool]) -> List[str]:
    """Validate a list of tools."""
    errors = []

    for tool_index, tool in enumerate(tools):
        if not isinstance(tool, BaseTool):
            errors.append(f"Tool {tool_index} must be a BaseTool instance")
        else:
            tool_errors = _validate_single_tool(tool, tool_index)
            errors.extend(tool_errors)

    return errors


def _validate_agent_tools(agent: BaseAgent) -> List[str]:
    """Validate agent tools."""
    try:
        tools = agent.get_tools()
        if not _tools_are_valid_list(tools):
            return ["get_tools() must return a list"]

        if not _agent_has_tools(tools):
            return ["Agent must provide at least one tool"]

        return validate_tools(tools)
    except Exception as e:
        return [f"Error calling get_tools(): {e}"]


def _tools_are_valid_list(tools: Any) -> bool:
    """Check if tools is a valid list."""
    return isinstance(tools, list)


def _agent_has_tools(tools: List[BaseTool]) -> bool:
    """Check if agent has at least one tool."""
    return bool(tools)


def validate_agent(agent: BaseAgent) -> List[str]:
    """Validate plugin agent implementation."""
    errors = []
    required_methods = ["get_tools", "bind_model", "initialize", "create_agent_node", "should_continue"]

    for method_name in required_methods:
        if not _method_exists_and_callable(agent, method_name):
            errors.append(f"Agent must implement {method_name}() method")

    if not errors:
        errors.extend(_validate_agent_tools(agent))

    return errors


def _validate_metadata(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate plugin metadata."""
    try:
        metadata = plugin_class.get_metadata()
        if not _metadata_is_valid_instance(metadata):
            return ["get_metadata() must return PluginMetadata instance"]
        return validate_metadata(metadata)
    except Exception as e:
        return [f"Error calling get_metadata(): {e}"]


def _metadata_is_valid_instance(metadata: Any) -> bool:
    """Check if metadata is a valid PluginMetadata instance."""
    return isinstance(metadata, PluginMetadata)


def _validate_agent_creation(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate agent creation."""
    try:
        agent = plugin_class.create_agent()
        if not _agent_is_valid_instance(agent):
            return ["create_agent() must return BaseAgent instance"]
        return validate_agent(agent)
    except Exception as e:
        return [f"Error calling create_agent(): {e}"]


def _agent_is_valid_instance(agent: Any) -> bool:
    """Check if agent is a valid BaseAgent instance."""
    return isinstance(agent, BaseAgent)


def validate_plugin_structure_shallow(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate class shape and metadata without instantiating the agent."""
    errors = []

    if not _plugin_is_valid_class(plugin_class):
        errors.append("Plugin must be a class")
        return errors

    if not _plugin_inherits_from_base(plugin_class):
        errors.append("Plugin must inherit from BasePlugin")

    errors.extend(_validate_required_methods(plugin_class))

    if not errors:
        errors.extend(_validate_metadata(plugin_class))

    return errors


def _plugin_is_valid_class(plugin_class: Any) -> bool:
    """Check if plugin is a valid class."""
    return inspect.isclass(plugin_class)


def _plugin_inherits_from_base(plugin_class: Type[BasePlugin]) -> bool:
    """Check if plugin inherits from BasePlugin."""
    return issubclass(plugin_class, BasePlugin)


def validate_plugin_structure(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate that a plugin class implements the required interface."""
    errors = []

    if not _plugin_is_valid_class(plugin_class):
        errors.append("Plugin must be a class")
        return errors

    if not _plugin_inherits_from_base(plugin_class):
        errors.append("Plugin must inherit from BasePlugin")

    errors.extend(_validate_required_methods(plugin_class))

    if not errors:
        errors.extend(_validate_metadata(plugin_class))
        errors.extend(_validate_agent_creation(plugin_class))

    return errors

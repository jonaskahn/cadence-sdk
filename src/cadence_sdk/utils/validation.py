"""Validation utilities for Cadence plugins."""

import inspect
from typing import List, Type

from langchain_core.tools import BaseTool

from ..base.agent import BaseAgent
from ..base.metadata import PluginMetadata
from ..base.plugin import BasePlugin


def validate_plugin_structure(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate that a plugin class implements the required interface."""
    errors = []

    if not inspect.isclass(plugin_class):
        errors.append("Plugin must be a class")
        return errors

    if not issubclass(plugin_class, BasePlugin):
        errors.append("Plugin must inherit from BasePlugin")

    errors.extend(_validate_required_methods(plugin_class))

    if not errors:
        errors.extend(_validate_metadata(plugin_class))
        errors.extend(_validate_agent_creation(plugin_class))

    return errors


def validate_plugin_structure_shallow(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate class shape and metadata without instantiating the agent."""
    errors = []

    if not inspect.isclass(plugin_class):
        errors.append("Plugin must be a class")
        return errors

    if not issubclass(plugin_class, BasePlugin):
        errors.append("Plugin must inherit from BasePlugin")

    errors.extend(_validate_required_methods(plugin_class))

    if not errors:
        errors.extend(_validate_metadata(plugin_class))

    return errors


def _validate_required_methods(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate that required methods exist and are callable."""
    errors = []

    required_methods = ["get_metadata", "create_agent"]
    for method_name in required_methods:
        if not hasattr(plugin_class, method_name):
            errors.append(f"Plugin must implement {method_name}() method")
        elif not callable(getattr(plugin_class, method_name)):
            errors.append(f"{method_name} must be callable")

    return errors


def _validate_metadata(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate plugin metadata."""
    try:
        metadata = plugin_class.get_metadata()
        if not isinstance(metadata, PluginMetadata):
            return ["get_metadata() must return PluginMetadata instance"]
        return validate_metadata(metadata)
    except Exception as e:
        return [f"Error calling get_metadata(): {e}"]


def _validate_agent_creation(plugin_class: Type[BasePlugin]) -> List[str]:
    """Validate agent creation."""
    try:
        agent = plugin_class.create_agent()
        if not isinstance(agent, BaseAgent):
            return ["create_agent() must return BasePluginAgent instance"]
        return validate_agent(agent)
    except Exception as e:
        return [f"Error calling create_agent(): {e}"]


def validate_metadata(metadata: PluginMetadata) -> List[str]:
    """Validate plugin metadata."""
    errors = []

    if not metadata.name or not metadata.name.strip():
        errors.append("Plugin name cannot be empty")

    if not metadata.version or not metadata.version.strip():
        errors.append("Plugin version cannot be empty")

    if not metadata.description or not metadata.description.strip():
        errors.append("Plugin description cannot be empty")

    if not metadata.capabilities:
        errors.append("Plugin must define at least one capability")

    valid_types = {"specialized", "general", "utility"}
    if metadata.agent_type not in valid_types:
        errors.append(f"Invalid agent_type: {metadata.agent_type}. Must be one of {valid_types}")

    if not _is_valid_version_format(metadata.version):
        errors.append(f"Invalid version format: {metadata.version}")

    return errors


def _is_valid_version_format(version: str) -> bool:
    """Check if version string follows semantic versioning format."""
    if not version:
        return False

    parts = version.split(".")
    if len(parts) < 2:
        return False

    for part in parts:
        if not part.isdigit():
            return False

    return True


def validate_agent(agent: BaseAgent) -> List[str]:
    """Validate plugin agent implementation."""
    errors = []

    if not hasattr(agent, "get_tools"):
        errors.append("Agent must implement get_tools() method")
    elif not callable(getattr(agent, "get_tools")):
        errors.append("get_tools must be callable")

    if not hasattr(agent, "bind_model"):
        errors.append("Agent must implement bind_model() method")
    elif not callable(getattr(agent, "bind_model")):
        errors.append("bind_model must be callable")

    if not hasattr(agent, "initialize"):
        errors.append("Agent must implement initialize() method")
    elif not callable(getattr(agent, "initialize")):
        errors.append("initialize must be callable")

    if not hasattr(agent, "create_agent_node"):
        errors.append("Agent must implement create_agent_node() method")
    elif not callable(getattr(agent, "create_agent_node")):
        errors.append("create_agent_node must be callable")

    if not hasattr(agent, "should_continue"):
        errors.append("Agent must implement should_continue() method")
    elif not callable(getattr(agent, "should_continue")):
        errors.append("should_continue must be callable")

    if not errors:
        errors.extend(_validate_agent_tools(agent))

    return errors


def _validate_agent_tools(agent: BaseAgent) -> List[str]:
    """Validate agent tools."""
    try:
        tools = agent.get_tools()
        if not isinstance(tools, list):
            return ["get_tools() must return a list"]

        if not tools:
            return ["Agent must provide at least one tool"]

        return validate_tools(tools)
    except Exception as e:
        return [f"Error calling get_tools(): {e}"]


def validate_tools(tools: List[BaseTool]) -> List[str]:
    """Validate a list of tools."""
    errors = []

    for i, tool in enumerate(tools):
        if not isinstance(tool, BaseTool):
            errors.append(f"Tool {i} must be a BaseTool instance")
        else:
            tool_errors = _validate_single_tool(tool, i)
        errors.extend(tool_errors)

    return errors


def _validate_single_tool(tool: BaseTool, index: int) -> List[str]:
    """Validate a single tool."""
    errors = []

    if not tool.name or not tool.name.strip():
        errors.append(f"Tool {index} must have a name")

    if not tool.description or not tool.description.strip():
        errors.append(f"Tool {index} must have a description")

    if not hasattr(tool, "func") or not callable(getattr(tool, "func")):
        errors.append(f"Tool {index} must have a callable func attribute")

    return errors

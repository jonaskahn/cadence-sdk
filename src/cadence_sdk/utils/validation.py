"""Plugin validation utilities.

This module provides validation functions for checking plugin structure
and requirements.
"""

from typing import List, Optional, Tuple, Type

from packaging import version as pkg_version

from ..base import BaseAgent, BasePlugin, PluginMetadata


def validate_plugin_structure_shallow(plugin_class: Type) -> Tuple[bool, List[str]]:
    """Perform fast shallow validation of plugin structure.

    This performs only quick checks without instantiating the plugin or agent:
    - Is it a BasePlugin subclass?
    - Does it have required methods?
    - Does metadata have required fields?

    Args:
        plugin_class: Plugin class to validate

    Returns:
        Tuple of (is_valid, error_messages)

    Example:
        is_valid, errors = validate_plugin_structure_shallow(MyPlugin)
        if not is_valid:
            print("Validation errors:", errors)
    """
    errors = []

    base_class_error = _validate_base_plugin_subclass(plugin_class)
    if base_class_error:
        errors.append(base_class_error)
        return False, errors

    method_errors = _validate_required_methods(plugin_class)
    errors.extend(method_errors)

    if errors:
        return False, errors

    metadata_errors = _validate_plugin_metadata(plugin_class)
    errors.extend(metadata_errors)

    is_valid = len(errors) == 0
    return is_valid, errors


def _validate_base_plugin_subclass(plugin_class: Type) -> Optional[str]:
    """Validate that class is a BasePlugin subclass.

    Args:
        plugin_class: Class to validate

    Returns:
        Error message if invalid, None otherwise
    """
    try:
        if not issubclass(plugin_class, BasePlugin):
            return f"{plugin_class.__name__} must inherit from BasePlugin"
    except TypeError:
        return f"{plugin_class} is not a class"
    return None


def _validate_required_methods(plugin_class: Type) -> List[str]:
    """Validate that plugin has required methods.

    Args:
        plugin_class: Plugin class to validate

    Returns:
        List of error messages
    """
    errors = []

    if not hasattr(plugin_class, "get_metadata"):
        errors.append("Plugin must implement get_metadata() method")

    if not hasattr(plugin_class, "create_agent"):
        errors.append("Plugin must implement create_agent() method")

    return errors


def _validate_plugin_metadata(plugin_class: Type) -> List[str]:
    """Validate plugin metadata structure and content.

    Args:
        plugin_class: Plugin class to validate

    Returns:
        List of error messages
    """
    errors = []

    try:
        metadata = plugin_class.get_metadata()

        if not isinstance(metadata, PluginMetadata):
            errors.append(
                f"get_metadata() must return PluginMetadata, got {type(metadata)}"
            )
            return errors

        errors.extend(_validate_metadata_fields(metadata))

    except Exception as e:
        errors.append(f"Error calling get_metadata(): {str(e)}")

    return errors


def _validate_metadata_fields(metadata: PluginMetadata) -> List[str]:
    """Validate metadata required fields.

    Args:
        metadata: Plugin metadata to validate

    Returns:
        List of error messages
    """
    errors = []

    if not metadata.name:
        errors.append("Plugin metadata must have non-empty 'name'")

    if not metadata.version:
        errors.append("Plugin metadata must have non-empty 'version'")

    if not metadata.description:
        errors.append("Plugin metadata must have non-empty 'description'")

    try:
        pkg_version.parse(metadata.version)
    except pkg_version.InvalidVersion:
        errors.append(f"Invalid version format: {metadata.version}")

    return errors


def validate_plugin_structure(plugin_class: Type) -> Tuple[bool, List[str]]:
    """Perform deep validation of plugin structure.

    This performs comprehensive validation including:
    - Shallow validation checks
    - Create agent instance and check interface
    - Validate tools returned by agent
    - Check SDK version compatibility
    - Validate dependencies

    Args:
        plugin_class: Plugin class to validate

    Returns:
        Tuple of (is_valid, error_messages)

    Example:
        is_valid, errors = validate_plugin_structure(MyPlugin)
        if not is_valid:
            for error in errors:
                print(f"ERROR: {error}")
    """
    is_valid, errors = validate_plugin_structure_shallow(plugin_class)
    if not is_valid:
        return False, errors

    metadata = plugin_class.get_metadata()
    agent = _validate_agent_creation(plugin_class, errors)

    if agent is None:
        return False, errors

    _validate_agent_interface(agent, errors)
    _validate_agent_tools(agent, errors)
    _validate_agent_system_prompt(agent, errors)
    _validate_sdk_version(metadata, errors)
    _validate_plugin_dependencies(plugin_class, errors)

    is_valid = len(errors) == 0
    return is_valid, errors


def _validate_agent_creation(
    plugin_class: Type, errors: List[str]
) -> Optional[BaseAgent]:
    """Validate agent creation from plugin.

    Args:
        plugin_class: Plugin class
        errors: List to append errors to

    Returns:
        Created agent or None if creation failed
    """
    try:
        agent = plugin_class.create_agent()

        if not isinstance(agent, BaseAgent):
            errors.append(
                f"create_agent() must return BaseAgent instance, got {type(agent)}"
            )
            return None

        return agent

    except Exception as e:
        errors.append(f"Error calling create_agent(): {str(e)}")
        return None


def _validate_agent_interface(agent: BaseAgent, errors: List[str]) -> None:
    """Validate agent has required interface methods.

    Args:
        agent: Agent to validate
        errors: List to append errors to
    """
    if not hasattr(agent, "get_tools"):
        errors.append("Agent must implement get_tools() method")

    if not hasattr(agent, "get_system_prompt"):
        errors.append("Agent must implement get_system_prompt() method")


def _validate_agent_tools(agent: BaseAgent, errors: List[str]) -> None:
    """Validate agent tools structure.

    Args:
        agent: Agent to validate
        errors: List to append errors to
    """
    try:
        tools = agent.get_tools()

        if not isinstance(tools, list):
            errors.append(f"Agent.get_tools() must return list, got {type(tools)}")
            return

        from ..types import UvTool

        for i, tool in enumerate(tools):
            if not isinstance(tool, UvTool):
                errors.append(
                    f"Tool at index {i} is not a UvTool instance: {type(tool)}"
                )

    except Exception as e:
        errors.append(f"Error calling agent.get_tools(): {str(e)}")


def _validate_agent_system_prompt(agent: BaseAgent, errors: List[str]) -> None:
    """Validate agent system prompt.

    Args:
        agent: Agent to validate
        errors: List to append errors to
    """
    try:
        prompt = agent.get_system_prompt()

        if not isinstance(prompt, str):
            errors.append(
                f"Agent.get_system_prompt() must return str, got {type(prompt)}"
            )
        elif not prompt.strip():
            errors.append("Agent.get_system_prompt() returned empty string")

    except Exception as e:
        errors.append(f"Error calling agent.get_system_prompt(): {str(e)}")


def _validate_sdk_version(metadata: PluginMetadata, errors: List[str]) -> None:
    """Validate SDK version compatibility.

    Args:
        metadata: Plugin metadata
        errors: List to append errors to
    """
    try:
        sdk_version_req = metadata.sdk_version

        if not sdk_version_req:
            errors.append("Plugin metadata must specify sdk_version")

    except Exception as e:
        errors.append(f"Error checking SDK version: {str(e)}")


def _validate_plugin_dependencies(plugin_class: Type, errors: List[str]) -> None:
    """Validate plugin dependencies.

    Args:
        plugin_class: Plugin class
        errors: List to append errors to
    """
    try:
        dependency_errors = plugin_class.validate_dependencies()

        if dependency_errors:
            errors.extend([f"Dependency error: {err}" for err in dependency_errors])

    except Exception as e:
        errors.append(f"Error in validate_dependencies(): {str(e)}")


def validate_sdk_version_compatibility(required: str, current: str) -> Tuple[bool, str]:
    """Check if current SDK version satisfies requirement.

    Args:
        required: Version requirement string (e.g., ">=2.0.0,<3.0.0")
        current: Current SDK version (e.g., "2.1.0")

    Returns:
        Tuple of (is_compatible, error_message)

    Example:
        is_compat, msg = validate_sdk_version_compatibility(
            ">=2.0.0,<3.0.0",
            "2.1.0"
        )
    """
    try:
        from packaging import specifiers

        spec_set = specifiers.SpecifierSet(required)
        current_ver = pkg_version.parse(current)

        if current_ver in spec_set:
            return True, ""
        else:
            return (
                False,
                f"SDK version {current} does not satisfy requirement {required}",
            )

    except Exception as e:
        return False, f"Error checking version compatibility: {str(e)}"

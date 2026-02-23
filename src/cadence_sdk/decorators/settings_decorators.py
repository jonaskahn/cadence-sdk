"""Settings decorators for Cadence SDK plugins.

This module provides decorators for declaring plugin configuration
requirements.
"""

from typing import Any, Callable, Dict, List, Literal, Optional

SettingType = Literal["str", "int", "float", "bool", "list", "dict"]

VALID_SETTING_TYPES = {"str", "int", "float", "bool", "list", "dict"}


def plugin_settings(settings_list: List[Dict[str, Any]]) -> Callable:
    """Decorator to declare plugin configuration schema.

    This decorator allows plugins to declare their configuration requirements
    in a structured way. The framework will validate and provide these settings
    to the agent's initialize() method.

    Args:
        settings_list: List of setting definitions. Each setting dict should have:
            - key (str): Setting key name (machine-readable identifier)
            - name (str, optional): Display name shown in UI (defaults to key)
            - type (str): Type ('str', 'int', 'float', 'bool', 'list', 'dict')
            - default (any, optional): Default value if not provided
            - description (str): Human-readable description
            - required (bool, default False): Whether setting is mandatory
            - sensitive (bool, default False): Whether to mask in logs/UI

    Returns:
        Decorated plugin class with settings schema attached

    Example:
        @plugin_settings([
            {
                "key": "api_key",
                "name": "API Key",
                "type": "str",
                "required": True,
                "sensitive": True,
                "description": "API key for the service"
            },
            {
                "key": "max_results",
                "name": "Max Results",
                "type": "int",
                "default": 10,
                "description": "Maximum number of results to return"
            },
            {
                "key": "enable_caching",
                "name": "Enable Caching",
                "type": "bool",
                "default": True,
                "description": "Enable response caching"
            }
        ])
        class MyPlugin(BasePlugin):
            ...

    Note:
        - Settings are passed to agent.initialize(config) as a dict
        - Required settings without defaults must be provided by the framework
        - Sensitive settings are encrypted at rest and masked in logs/UI
        - 'name' is used as the display label in UI; if omitted it defaults to 'key'
    """

    def decorator(cls: type) -> type:
        """Inner decorator that attaches settings schema to class."""
        _validate_settings_schema(settings_list)
        normalized = [{**s, "name": s.get("name", s["key"])} for s in settings_list]
        cls._cadence_settings_schema = normalized

        original_get_settings = getattr(cls, "get_settings_schema", None)
        cls.get_settings_schema = _create_settings_schema_method(
            normalized, original_get_settings
        )

        return cls

    return decorator


def _create_settings_schema_method(
    settings_list: List[Dict[str, Any]], original_method: Optional[Callable]
) -> staticmethod:
    """Create settings schema method for plugin class.

    Args:
        settings_list: Settings schema from decorator
        original_method: Existing get_settings_schema method (if any)

    Returns:
        staticmethod that returns settings schema
    """
    if original_method and callable(original_method):

        def combined_get_settings():
            method_settings = original_method()
            return settings_list + method_settings

        return staticmethod(combined_get_settings)
    else:

        def get_settings_schema() -> List[Dict[str, Any]]:
            return settings_list

        return staticmethod(get_settings_schema)


def _validate_settings_schema(settings_list: List[Dict[str, Any]]) -> None:
    """Validate settings schema format.

    Args:
        settings_list: Settings schema to validate

    Raises:
        ValueError: If schema is invalid
    """
    if not isinstance(settings_list, list):
        raise ValueError("settings_list must be a list")

    seen_keys = set()

    for i, setting in enumerate(settings_list):
        if not isinstance(setting, dict):
            raise ValueError(f"Setting at index {i} must be a dict")

        _validate_setting_required_fields(setting, i)

        key = setting["key"]
        setting_type = setting["type"]

        _validate_unique_key(key, seen_keys)
        seen_keys.add(key)

        _validate_setting_type(setting_type, key)
        _validate_boolean_flags(setting, key)
        _validate_default_value_type(setting, setting_type, key)


def _validate_setting_required_fields(setting: Dict[str, Any], index: int) -> None:
    """Validate setting has required fields.

    Args:
        setting: Setting dictionary
        index: Setting index for error messages

    Raises:
        ValueError: If required fields are missing
    """
    if "key" not in setting:
        raise ValueError(f"Setting at index {index} missing 'key' field")

    if "type" not in setting:
        raise ValueError(f"Setting at index {index} missing 'type' field")

    if "description" not in setting:
        raise ValueError(f"Setting at index {index} missing 'description' field")


def _validate_unique_key(key: str, seen_keys: set) -> None:
    """Validate setting key is unique.

    Args:
        key: Setting key
        seen_keys: Set of already seen keys

    Raises:
        ValueError: If key is duplicate
    """
    if key in seen_keys:
        raise ValueError(f"Duplicate setting key: {key}")


def _validate_setting_type(setting_type: str, key: str) -> None:
    """Validate setting type is valid.

    Args:
        setting_type: Type string
        key: Setting key for error message

    Raises:
        ValueError: If type is invalid
    """
    if setting_type not in VALID_SETTING_TYPES:
        raise ValueError(
            f"Invalid type '{setting_type}' for setting '{key}'. "
            f"Must be one of: {VALID_SETTING_TYPES}"
        )


def _validate_boolean_flags(setting: Dict[str, Any], key: str) -> None:
    """Validate required and sensitive flags are booleans.

    Args:
        setting: Setting dictionary
        key: Setting key for error message

    Raises:
        ValueError: If flags are not boolean
    """
    if "required" in setting and not isinstance(setting["required"], bool):
        raise ValueError(f"'required' field for setting '{key}' must be bool")

    if "sensitive" in setting and not isinstance(setting["sensitive"], bool):
        raise ValueError(f"'sensitive' field for setting '{key}' must be bool")


def _validate_default_value_type(
    setting: Dict[str, Any], setting_type: str, key: str
) -> None:
    """Validate default value type matches declared type.

    Args:
        setting: Setting dictionary
        setting_type: Declared type string
        key: Setting key for error message

    Raises:
        ValueError: If default value type doesn't match
    """
    if "default" not in setting:
        return

    default_value = setting["default"]
    expected_type = _get_python_type(setting_type)

    if default_value is not None and not isinstance(default_value, expected_type):
        raise ValueError(
            f"Default value for setting '{key}' has type {type(default_value).__name__}, "
            f"but declared type is '{setting_type}'"
        )


def _get_python_type(type_str: str) -> type:
    """Map type string to Python type.

    Args:
        type_str: Type string

    Returns:
        Python type class
    """
    type_map = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
    }
    return type_map[type_str]


def get_plugin_settings_schema(plugin_class: type) -> List[Dict[str, Any]]:
    """Get settings schema from a plugin class.

    This is a utility function to retrieve the settings schema that was
    attached by the @plugin_settings decorator or via get_settings_schema() method.

    Args:
        plugin_class: Plugin class to inspect

    Returns:
        List of setting definitions, or empty list if none defined

    Example:
        schema = get_plugin_settings_schema(MyPlugin)
        for setting in schema:
            print(f"{setting['name']} ({setting['key']}): {setting['description']}")
    """
    if hasattr(plugin_class, "_cadence_settings_schema"):
        return plugin_class._cadence_settings_schema

    if hasattr(plugin_class, "get_settings_schema"):
        method = getattr(plugin_class, "get_settings_schema")
        if callable(method):
            return method()

    return []

"""Tests for plugin_settings decorator."""

import pytest
from cadence_sdk import BasePlugin, PluginMetadata, plugin_settings
from cadence_sdk.decorators.settings_decorators import get_plugin_settings_schema

from .conftest import MinimalAgent


@plugin_settings(
    [
        {
            "key": "api_key",
            "type": "str",
            "required": True,
            "sensitive": True,
            "description": "API key",
        },
        {
            "key": "max_results",
            "type": "int",
            "default": 10,
            "description": "Max results",
        },
    ]
)
class SettingsPlugin(BasePlugin):
    """Plugin with @plugin_settings for testing."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.settings",
            name="Settings Plugin",
            version="1.0.0",
            description="Plugin with settings",
        )

    @staticmethod
    def create_agent():
        return MinimalAgent()


class TestPluginSettingsDecorator:
    """Tests for @plugin_settings decorator."""

    def test_attaches_settings_schema_to_class(self):
        """@plugin_settings attaches _cadence_settings_schema to class."""
        assert hasattr(SettingsPlugin, "_cadence_settings_schema")
        schema = SettingsPlugin._cadence_settings_schema
        assert len(schema) == 2
        keys = [s["key"] for s in schema]
        assert "api_key" in keys
        assert "max_results" in keys

    def test_get_settings_schema_returns_decorator_schema(self):
        """get_settings_schema returns schema from decorator."""
        schema = get_plugin_settings_schema(SettingsPlugin)
        assert len(schema) == 2
        api_key_setting = next(s for s in schema if s["key"] == "api_key")
        assert api_key_setting["type"] == "str"
        assert api_key_setting["required"] is True
        assert api_key_setting["sensitive"] is True

    def test_get_plugin_settings_schema_returns_empty_for_plain_plugin(self):
        """get_plugin_settings_schema returns empty list for plugin without decorator."""
        from .conftest import MinimalPlugin

        schema = get_plugin_settings_schema(MinimalPlugin)
        assert schema == []


class TestPluginSettingsValidation:
    """Tests for settings schema validation."""

    def test_rejects_non_list_settings(self):
        """plugin_settings raises ValueError for non-list."""
        with pytest.raises(ValueError, match="must be a list"):

            @plugin_settings("not a list")  # type: ignore
            class BadPlugin(BasePlugin):
                @staticmethod
                def get_metadata():
                    return PluginMetadata(
                        pid="x", name="x", version="1.0.0", description="x"
                    )

                @staticmethod
                def create_agent():
                    return MinimalAgent()

    def test_rejects_setting_missing_key(self):
        """plugin_settings raises ValueError when setting missing 'key'."""
        with pytest.raises(ValueError, match="missing 'key'"):

            @plugin_settings(
                [
                    {
                        "type": "str",
                        "description": "Missing key",
                    }
                ]
            )
            class BadPlugin(BasePlugin):
                @staticmethod
                def get_metadata():
                    return PluginMetadata(
                        pid="x", name="x", version="1.0.0", description="x"
                    )

                @staticmethod
                def create_agent():
                    return MinimalAgent()

    def test_rejects_invalid_setting_type(self):
        """plugin_settings raises ValueError for invalid type."""
        with pytest.raises(ValueError, match="Invalid type"):

            @plugin_settings(
                [
                    {
                        "key": "x",
                        "type": "invalid_type",
                        "description": "Bad type",
                    }
                ]
            )
            class BadPlugin(BasePlugin):
                @staticmethod
                def get_metadata():
                    return PluginMetadata(
                        pid="x", name="x", version="1.0.0", description="x"
                    )

                @staticmethod
                def create_agent():
                    return MinimalAgent()

"""Tests for plugin validation utilities."""

from cadence_sdk import validate_plugin_structure, validate_plugin_structure_shallow
from cadence_sdk.utils.validation import validate_sdk_version_compatibility

from .conftest import InvalidPluginNoCreateAgent, InvalidPluginNoMetadata, MinimalPlugin


class TestValidatePluginStructureShallow:
    """Tests for validate_plugin_structure_shallow."""

    def test_validates_minimal_plugin_successfully(self):
        """Shallow validation passes for valid MinimalPlugin."""
        is_valid, errors = validate_plugin_structure_shallow(MinimalPlugin)
        assert is_valid is True
        assert errors == []

    def test_rejects_class_not_inheriting_base_plugin(self):
        """Shallow validation rejects class not inheriting BasePlugin."""
        is_valid, errors = validate_plugin_structure_shallow(InvalidPluginNoMetadata)
        assert is_valid is False
        assert any("BasePlugin" in e for e in errors)

    def test_rejects_non_class(self):
        """Shallow validation rejects non-class (e.g. instance)."""
        is_valid, errors = validate_plugin_structure_shallow(MinimalPlugin())
        assert is_valid is False
        assert len(errors) > 0


class TestValidatePluginStructure:
    """Tests for validate_plugin_structure (deep validation)."""

    def test_rejects_plugin_with_abstract_create_agent(self):
        """Deep validation rejects plugin that does not implement create_agent."""
        is_valid, errors = validate_plugin_structure(InvalidPluginNoCreateAgent)
        assert is_valid is False
        assert any("create_agent" in e for e in errors)

    def test_validates_minimal_plugin_successfully(self):
        """Deep validation passes for valid MinimalPlugin."""
        is_valid, errors = validate_plugin_structure(MinimalPlugin)
        assert is_valid is True
        assert errors == []

    def test_deep_validation_includes_shallow_checks(self):
        """Deep validation fails on same errors as shallow."""
        is_valid, errors = validate_plugin_structure(InvalidPluginNoMetadata)
        assert is_valid is False
        assert len(errors) > 0


class TestValidateSdkVersionCompatibility:
    """Tests for validate_sdk_version_compatibility."""

    def test_compatible_version_returns_true(self):
        """validate_sdk_version_compatibility returns True for compatible version."""
        is_compat, msg = validate_sdk_version_compatibility(
            ">=3.0.0,<4.0.0",
            "3.1.0",
        )
        assert is_compat is True
        assert msg == ""

    def test_incompatible_version_returns_false(self):
        """validate_sdk_version_compatibility returns False for incompatible version."""
        is_compat, msg = validate_sdk_version_compatibility(
            ">=3.0.0,<4.0.0",
            "2.9.0",
        )
        assert is_compat is False
        assert "does not satisfy" in msg

    def test_invalid_requirement_returns_false_with_error(self):
        """validate_sdk_version_compatibility handles invalid requirement."""
        is_compat, msg = validate_sdk_version_compatibility(
            "invalid-requirement",
            "3.0.0",
        )
        assert is_compat is False
        assert len(msg) > 0

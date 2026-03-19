"""Tests for plugin validation utilities."""

import pytest
from cadence_sdk import validate_plugin_structure, validate_plugin_structure_shallow
from cadence_sdk.utils.validation import (
    _validate_agent_creation,
    _validate_agent_interface,
    _validate_agent_tools,
    _validate_metadata_fields,
    _validate_plugin_dependencies,
    _validate_sdk_version,
    validate_sdk_version_compatibility,
)
from .conftest import (
    AgentBadTools,
    AgentToolsRaises,
    InvalidPluginNoCreateAgent,
    InvalidPluginNoMetadata,
    MinimalAgent,
    MinimalPlugin,
    PluginCreateAgentRaises,
    PluginCreateAgentWrongType,
    PluginDepsRaises,
    PluginWithDepsError,
    make_raw_metadata,
)


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


class TestValidateMetadataFields:
    def test_empty_name_reported(self):
        m = make_raw_metadata(name="")
        errors = _validate_metadata_fields(m)
        assert any("name" in e for e in errors)

    def test_empty_version_reported(self):
        m = make_raw_metadata(version="")
        errors = _validate_metadata_fields(m)
        assert any("version" in e for e in errors)

    def test_empty_description_reported(self):
        m = make_raw_metadata(description="")
        errors = _validate_metadata_fields(m)
        assert any("description" in e for e in errors)

    def test_invalid_version_format_reported(self):
        m = make_raw_metadata(version="not_semver!!")
        errors = _validate_metadata_fields(m)
        assert any("version" in e.lower() or "invalid" in e.lower() for e in errors)


class TestValidateAgentCreation:
    def test_returns_agent_for_good_plugin(self):
        errors = []
        agent = _validate_agent_creation(MinimalPlugin, errors)
        assert agent is not None
        assert errors == []

    def test_returns_none_when_create_agent_raises(self):
        errors = []
        agent = _validate_agent_creation(PluginCreateAgentRaises, errors)
        assert agent is None
        assert len(errors) > 0

    def test_returns_none_when_create_agent_wrong_type(self):
        errors = []
        agent = _validate_agent_creation(PluginCreateAgentWrongType, errors)
        assert agent is None
        assert len(errors) > 0


class TestValidateAgentInterface:
    def test_no_errors_for_good_agent(self):
        errors = []
        _validate_agent_interface(MinimalAgent(), errors)
        assert errors == []

    def test_reports_missing_get_tools(self):
        import types

        agent = types.SimpleNamespace(get_system_prompt=lambda: "x")
        errors = []
        _validate_agent_interface(agent, errors)
        assert any("get_tools" in e for e in errors)

    @pytest.mark.skip(
        reason=(
            "BaseSpecializedAgent.get_system_prompt is abstract — Python's ABC prevents "
            "instantiation without it, so isinstance(..., BaseSpecializedAgent) and "
            "not hasattr(..., 'get_system_prompt') is unreachable in practice. "
            "The positive case (no error when implemented) is covered by "
            "test_no_errors_for_minimal_agent."
        )
    )
    def test_reports_missing_get_system_prompt(self):
        pass


class TestValidateAgentTools:
    def test_no_errors_for_good_agent(self):
        errors = []
        _validate_agent_tools(MinimalAgent(), errors)
        assert errors == []

    def test_reports_non_uvtool_items(self):
        errors = []
        _validate_agent_tools(AgentBadTools(), errors)
        assert len(errors) > 0

    def test_reports_get_tools_exception(self):
        errors = []
        _validate_agent_tools(AgentToolsRaises(), errors)
        assert len(errors) > 0

    def test_reports_non_list_return(self):
        import types

        agent = types.SimpleNamespace(get_tools=lambda: "not_a_list")
        errors = []
        _validate_agent_tools(agent, errors)
        assert len(errors) > 0


class TestValidateSdkVersionInternal:
    def test_no_errors_when_sdk_version_set(self):
        metadata = MinimalPlugin.get_metadata()
        errors = []
        _validate_sdk_version(metadata, errors)
        assert errors == []

    def test_reports_error_when_sdk_version_empty(self):
        metadata = MinimalPlugin.get_metadata()
        metadata.sdk_version = ""
        errors = []
        _validate_sdk_version(metadata, errors)
        assert len(errors) > 0


class TestValidatePluginDependenciesInternal:
    def test_no_errors_for_good_plugin(self):
        errors = []
        _validate_plugin_dependencies(MinimalPlugin, errors)
        assert errors == []

    def test_reports_dependency_errors(self):
        errors = []
        _validate_plugin_dependencies(PluginWithDepsError, errors)
        assert len(errors) > 0

    def test_reports_exception_from_validate_dependencies(self):
        errors = []
        _validate_plugin_dependencies(PluginDepsRaises, errors)
        assert len(errors) > 0


class TestValidatePluginStructureEdgeCases:
    def test_rejects_plugin_whose_create_agent_raises(self):
        is_valid, errors = validate_plugin_structure(PluginCreateAgentRaises)
        assert is_valid is False
        assert len(errors) > 0

    def test_reports_dependency_errors_in_deep_validation(self):
        is_valid, errors = validate_plugin_structure(PluginWithDepsError)
        assert is_valid is False
        assert any("Dependency" in e or "missing" in e for e in errors)

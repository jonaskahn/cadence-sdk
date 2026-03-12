"""Extended tests for validation utilities to increase coverage."""

from typing import List


from cadence_sdk import BaseAgent, BasePlugin, PluginMetadata, UvTool, uvtool
from cadence_sdk.utils.validation import (
    _validate_agent_creation,
    _validate_agent_interface,
    _validate_agent_system_prompt,
    _validate_agent_tools,
    _validate_metadata_fields,
    _validate_plugin_dependencies,
    _validate_sdk_version,
    validate_plugin_structure,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _GoodAgent(BaseAgent):
    def get_tools(self) -> List[UvTool]:
        @uvtool
        def noop(x: str) -> str:
            """No-op."""
            return x

        return [noop]

    def get_system_prompt(self) -> str:
        return "good prompt"

    def initialize(self, config):
        pass


class _GoodPlugin(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.ext.valid",
            name="Extended Valid",
            version="1.0.0",
            description="For extended validation tests",
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return _GoodAgent()


class _AgentEmptyPrompt(BaseAgent):
    def get_tools(self) -> List[UvTool]:
        return []

    def get_system_prompt(self) -> str:
        return "   "  # whitespace only — should fail

    def initialize(self, config):
        pass


class _AgentBadTools(BaseAgent):
    """Agent whose get_tools() returns non-UvTool items."""

    def get_tools(self):
        return ["not_a_tool"]

    def get_system_prompt(self) -> str:
        return "prompt"

    def initialize(self, config):
        pass


class _AgentToolsRaises(BaseAgent):
    """Agent whose get_tools() raises."""

    def get_tools(self):
        raise RuntimeError("boom")

    def get_system_prompt(self) -> str:
        return "prompt"

    def initialize(self, config):
        pass


class _AgentPromptRaises(BaseAgent):
    """Agent whose get_system_prompt() raises."""

    def get_tools(self) -> List[UvTool]:
        return []

    def get_system_prompt(self) -> str:
        raise RuntimeError("prompt boom")

    def initialize(self, config):
        pass


class _PluginCreateAgentRaises(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.ext.raises",
            name="Raises",
            version="1.0.0",
            description="create_agent raises",
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        raise RuntimeError("agent creation failed")


class _PluginCreateAgentWrongType(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.ext.wrongtype",
            name="WrongType",
            version="1.0.0",
            description="create_agent returns wrong type",
        )

    @staticmethod
    def create_agent():
        return "not_an_agent"


class _PluginWithDepsError(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.ext.depserr",
            name="DepsErr",
            version="1.0.0",
            description="has dep errors",
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return _GoodAgent()

    @staticmethod
    def validate_dependencies() -> List[str]:
        return ["missing_package not installed"]


class _PluginDepsRaises(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.ext.depsraises",
            name="DepsRaises",
            version="1.0.0",
            description="validate_dependencies raises",
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return _GoodAgent()

    @staticmethod
    def validate_dependencies():
        raise RuntimeError("deps check failed")


class _PluginNoSdkVersion(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        m = PluginMetadata(
            pid="com.ext.nosdk",
            name="NoSdk",
            version="1.0.0",
            description="no sdk version",
        )
        m.sdk_version = ""  # override to empty after construction
        return m

    @staticmethod
    def create_agent() -> BaseAgent:
        return _GoodAgent()


# ---------------------------------------------------------------------------
# _validate_metadata_fields
# ---------------------------------------------------------------------------


class TestValidateMetadataFields:
    def test_empty_name_reported(self):
        m = PluginMetadata.__new__(PluginMetadata)
        m.__dict__.update(
            pid="com.x.y",
            name="",
            version="1.0.0",
            description="d",
            capabilities=[],
            dependencies=[],
            agent_type="specialized",
            sdk_version=">=2.0.0",
            stateless=True,
        )
        errors = _validate_metadata_fields(m)
        assert any("name" in e for e in errors)

    def test_empty_version_reported(self):
        m = PluginMetadata.__new__(PluginMetadata)
        m.__dict__.update(
            pid="com.x.y",
            name="N",
            version="",
            description="d",
            capabilities=[],
            dependencies=[],
            agent_type="specialized",
            sdk_version=">=2.0.0",
            stateless=True,
        )
        errors = _validate_metadata_fields(m)
        assert any("version" in e for e in errors)

    def test_empty_description_reported(self):
        m = PluginMetadata.__new__(PluginMetadata)
        m.__dict__.update(
            pid="com.x.y",
            name="N",
            version="1.0.0",
            description="",
            capabilities=[],
            dependencies=[],
            agent_type="specialized",
            sdk_version=">=2.0.0",
            stateless=True,
        )
        errors = _validate_metadata_fields(m)
        assert any("description" in e for e in errors)

    def test_invalid_version_format_reported(self):
        m = PluginMetadata.__new__(PluginMetadata)
        m.__dict__.update(
            pid="com.x.y",
            name="N",
            version="not_semver!!",
            description="d",
            capabilities=[],
            dependencies=[],
            agent_type="specialized",
            sdk_version=">=2.0.0",
            stateless=True,
        )
        errors = _validate_metadata_fields(m)
        assert any("version" in e.lower() or "invalid" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# _validate_agent_creation
# ---------------------------------------------------------------------------


class TestValidateAgentCreation:
    def test_returns_agent_for_good_plugin(self):
        errors = []
        agent = _validate_agent_creation(_GoodPlugin, errors)
        assert agent is not None
        assert errors == []

    def test_returns_none_when_create_agent_raises(self):
        errors = []
        agent = _validate_agent_creation(_PluginCreateAgentRaises, errors)
        assert agent is None
        assert len(errors) > 0

    def test_returns_none_when_create_agent_wrong_type(self):
        errors = []
        agent = _validate_agent_creation(_PluginCreateAgentWrongType, errors)
        assert agent is None
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# _validate_agent_interface
# ---------------------------------------------------------------------------


class TestValidateAgentInterface:
    def test_no_errors_for_good_agent(self):
        errors = []
        _validate_agent_interface(_GoodAgent(), errors)
        assert errors == []

    def test_reports_missing_get_tools(self):
        """Manually remove get_tools via a mock object to test the check."""
        import types

        agent = types.SimpleNamespace(get_system_prompt=lambda: "x")
        errors = []
        _validate_agent_interface(agent, errors)
        assert any("get_tools" in e for e in errors)

    def test_reports_missing_get_system_prompt(self):
        import types

        agent = types.SimpleNamespace(get_tools=lambda: [])
        errors = []
        _validate_agent_interface(agent, errors)
        assert any("get_system_prompt" in e for e in errors)


# ---------------------------------------------------------------------------
# _validate_agent_tools
# ---------------------------------------------------------------------------


class TestValidateAgentTools:
    def test_no_errors_for_good_agent(self):
        agent = _GoodAgent()
        errors = []
        _validate_agent_tools(agent, errors)
        assert errors == []

    def test_reports_non_uvtool_items(self):
        agent = _AgentBadTools()
        errors = []
        _validate_agent_tools(agent, errors)
        assert len(errors) > 0

    def test_reports_get_tools_exception(self):
        agent = _AgentToolsRaises()
        errors = []
        _validate_agent_tools(agent, errors)
        assert len(errors) > 0

    def test_reports_non_list_return(self):
        import types

        agent = types.SimpleNamespace(get_tools=lambda: "not_a_list")
        errors = []
        _validate_agent_tools(agent, errors)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# _validate_agent_system_prompt
# ---------------------------------------------------------------------------


class TestValidateAgentSystemPrompt:
    def test_no_errors_for_good_agent(self):
        agent = _GoodAgent()
        errors = []
        _validate_agent_system_prompt(agent, errors)
        assert errors == []

    def test_reports_empty_prompt(self):
        agent = _AgentEmptyPrompt()
        errors = []
        _validate_agent_system_prompt(agent, errors)
        assert len(errors) > 0

    def test_reports_get_system_prompt_exception(self):
        agent = _AgentPromptRaises()
        errors = []
        _validate_agent_system_prompt(agent, errors)
        assert len(errors) > 0

    def test_reports_non_string_prompt(self):
        import types

        agent = types.SimpleNamespace(get_system_prompt=lambda: 42)
        errors = []
        _validate_agent_system_prompt(agent, errors)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# _validate_sdk_version
# ---------------------------------------------------------------------------


class TestValidateSdkVersionInternal:
    def test_no_errors_when_sdk_version_set(self):
        metadata = _GoodPlugin.get_metadata()
        errors = []
        _validate_sdk_version(metadata, errors)
        assert errors == []

    def test_reports_error_when_sdk_version_empty(self):
        metadata = _GoodPlugin.get_metadata()
        metadata.sdk_version = ""
        errors = []
        _validate_sdk_version(metadata, errors)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# _validate_plugin_dependencies
# ---------------------------------------------------------------------------


class TestValidatePluginDependenciesInternal:
    def test_no_errors_for_good_plugin(self):
        errors = []
        _validate_plugin_dependencies(_GoodPlugin, errors)
        assert errors == []

    def test_reports_dependency_errors(self):
        errors = []
        _validate_plugin_dependencies(_PluginWithDepsError, errors)
        assert len(errors) > 0

    def test_reports_exception_from_validate_dependencies(self):
        errors = []
        _validate_plugin_dependencies(_PluginDepsRaises, errors)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# validate_plugin_structure (deep) — edge cases
# ---------------------------------------------------------------------------


class TestValidatePluginStructureEdgeCases:
    def test_rejects_plugin_whose_create_agent_raises(self):
        is_valid, errors = validate_plugin_structure(_PluginCreateAgentRaises)
        assert is_valid is False
        assert len(errors) > 0

    def test_reports_dependency_errors_in_deep_validation(self):
        is_valid, errors = validate_plugin_structure(_PluginWithDepsError)
        assert is_valid is False
        assert any("Dependency" in e or "missing" in e for e in errors)

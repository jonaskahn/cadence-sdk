"""Pytest fixtures and shared test utilities for Cadence SDK tests."""

from typing import List

import pytest
from cadence_sdk import BaseAgent, BasePlugin, PluginMetadata, UvTool, uvtool


class MinimalAgent(BaseAgent):
    """Minimal agent for testing."""

    DEFAULT_SYSTEM_PROMPT = "You are a minimal test agent."

    def __init__(self):
        self._tool = self._create_tool()
        self._system_prompt = None

    def _create_tool(self) -> UvTool:
        @uvtool
        def echo(text: str) -> str:
            """Echo the input text."""
            return text

        return echo

    def get_tools(self) -> List[UvTool]:
        return [self._tool]

    def get_system_prompt(self) -> str:
        return self._system_prompt or self.DEFAULT_SYSTEM_PROMPT

    def initialize(self, config):
        self._system_prompt = config.get("system_prompt")


class MinimalPlugin(BasePlugin):
    """Minimal plugin for testing."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.minimal",
            name="Minimal Plugin",
            version="1.0.0",
            description="Minimal plugin for tests",
            capabilities=["echo"],
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return MinimalAgent()


class MinimalPluginV2(BasePlugin):
    """Same pid as MinimalPlugin but higher version."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.minimal",
            name="Minimal Plugin",
            version="2.0.0",
            description="Minimal plugin v2 for tests",
            capabilities=["echo"],
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return MinimalAgent()


class InvalidPluginNoMetadata:
    """Class that is not a BasePlugin - for validation tests."""

    @staticmethod
    def create_agent():
        return MinimalAgent()


class InvalidPluginNoCreateAgent(BasePlugin):
    """Plugin missing create_agent - for validation tests."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.invalid",
            name="Invalid",
            version="1.0.0",
            description="Missing create_agent",
        )


@pytest.fixture
def minimal_plugin():
    """Provide MinimalPlugin class for tests."""
    return MinimalPlugin


@pytest.fixture
def minimal_agent():
    """Provide MinimalAgent instance for tests."""
    return MinimalAgent()


@pytest.fixture
def plugin_registry():
    """Provide a clean PluginRegistry instance for tests."""
    from cadence_sdk import PluginRegistry

    registry = PluginRegistry.instance()
    registry.clear_all()
    yield registry
    registry.clear_all()


class AgentEmptyPrompt(BaseAgent):
    def get_tools(self) -> List[UvTool]:
        return []

    def get_system_prompt(self) -> str:
        return "   "

    def initialize(self, config):
        pass


class AgentBadTools(BaseAgent):
    def get_tools(self):
        return ["not_a_tool"]

    def get_system_prompt(self) -> str:
        return "prompt"

    def initialize(self, config):
        pass


class AgentToolsRaises(BaseAgent):
    def get_tools(self):
        raise RuntimeError("boom")

    def get_system_prompt(self) -> str:
        return "prompt"

    def initialize(self, config):
        pass


class AgentPromptRaises(BaseAgent):
    def get_tools(self) -> List[UvTool]:
        return []

    def get_system_prompt(self) -> str:
        raise RuntimeError("prompt boom")

    def initialize(self, config):
        pass


class PluginCreateAgentRaises(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.raises",
            name="Raises",
            version="1.0.0",
            description="create_agent raises",
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        raise RuntimeError("agent creation failed")


class PluginCreateAgentWrongType(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.wrongtype",
            name="WrongType",
            version="1.0.0",
            description="create_agent returns wrong type",
        )

    @staticmethod
    def create_agent():
        return "not_an_agent"


class PluginWithDepsError(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.depserr",
            name="DepsErr",
            version="1.0.0",
            description="has dep errors",
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return MinimalAgent()

    @staticmethod
    def validate_dependencies() -> List[str]:
        return ["missing_package not installed"]


class PluginDepsRaises(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.depsraises",
            name="DepsRaises",
            version="1.0.0",
            description="validate_dependencies raises",
        )

    @staticmethod
    def create_agent() -> BaseAgent:
        return MinimalAgent()

    @staticmethod
    def validate_dependencies():
        raise RuntimeError("deps check failed")


class PluginNoSdkVersion(BasePlugin):
    @staticmethod
    def get_metadata() -> PluginMetadata:
        m = PluginMetadata(
            pid="com.test.nosdk",
            name="NoSdk",
            version="1.0.0",
            description="no sdk version",
        )
        m.sdk_version = ""
        return m

    @staticmethod
    def create_agent() -> BaseAgent:
        return MinimalAgent()


def make_raw_metadata(**overrides) -> PluginMetadata:
    """Build a PluginMetadata bypassing __post_init__ validation."""
    defaults = dict(
        pid="com.x.y",
        name="N",
        version="1.0.0",
        description="d",
        capabilities=[],
        dependencies=[],
        agent_type="specialized",
        sdk_version=">=2.0.0",
        stateless=True,
    )
    m = PluginMetadata.__new__(PluginMetadata)
    m.__dict__.update({**defaults, **overrides})
    return m


PLUGIN_SRC = '''\
from cadence_sdk import BasePlugin, BaseAgent, PluginMetadata, uvtool

class _DiscAgent(BaseAgent):
    def get_tools(self):
        @uvtool
        def noop(x: str) -> str:
            """noop"""
            return x
        return [noop]
    def get_system_prompt(self):
        return "x"

class DiscPlugin(BasePlugin):
    @staticmethod
    def get_metadata():
        return PluginMetadata(
            pid="{pid}",
            name="Disc",
            version="{version}",
            description="discovery ext test",
        )
    @staticmethod
    def create_agent():
        return _DiscAgent()
'''


def write_plugin(
    directory,
    pid: str = "com.disc.ext",
    version: str = "1.0.0",
) -> None:
    """Write a minimal plugin.py into directory (created if needed)."""
    from pathlib import Path

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "plugin.py").write_text(PLUGIN_SRC.format(pid=pid, version=version))

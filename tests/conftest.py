"""Pytest fixtures and shared test utilities for Cadence SDK tests."""

from typing import List

import pytest
from cadence_sdk import BaseAgent, BasePlugin, PluginMetadata, UvTool, uvtool


class MinimalAgent(BaseAgent):
    """Minimal agent for testing."""

    def __init__(self):
        self._tool = self._create_tool()

    def _create_tool(self) -> UvTool:
        @uvtool
        def echo(text: str) -> str:
            """Echo the input text."""
            return text

        return echo

    def get_tools(self) -> List[UvTool]:
        return [self._tool]

    def get_system_prompt(self) -> str:
        return "You are a minimal test agent."


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

"""Tests for Loggable mixin."""

import logging

from cadence_sdk import BasePlugin, Loggable, PluginMetadata

from .conftest import MinimalAgent


class LoggablePlugin(BasePlugin, Loggable):
    """Plugin with Loggable mixin for testing."""

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            pid="com.test.loggable",
            name="Loggable Plugin",
            version="1.0.0",
            description="Plugin with logging",
        )

    @staticmethod
    def create_agent():
        return MinimalAgent()


class TestLoggable:
    """Tests for Loggable mixin."""

    def test_logger_property_returns_logger(self):
        """Loggable provides logger property with Logger instance."""
        plugin = LoggablePlugin()
        logger = plugin.logger
        assert isinstance(logger, logging.Logger)
        assert "LoggablePlugin" in logger.name

    def test_logger_is_cached_on_repeated_access(self):
        """Logger is cached - same instance on repeated access."""
        plugin = LoggablePlugin()
        assert plugin.logger is plugin.logger

    def test_set_log_level_accepts_level(self):
        """set_log_level accepts logging level constant."""
        plugin = LoggablePlugin()
        plugin.set_log_level(logging.DEBUG)
        assert plugin.logger.level == logging.DEBUG

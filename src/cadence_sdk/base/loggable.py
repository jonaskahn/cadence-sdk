"""Logging mixin for Cadence SDK classes."""

import logging
from typing import Optional


class Loggable:
    """Mixin class providing standardized logging capabilities.

    This mixin provides a logger property that plugin classes can use
    for consistent logging across the SDK.

    Usage:
        class MyPlugin(BasePlugin, Loggable):
            def some_method(self):
                self.logger.info("Doing something")
                self.logger.debug("Debug details")
    """

    _logger: Optional[logging.Logger] = None

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class.

        Creates a logger on first access, named after the class's module and name.
        """
        if self._logger is None:
            self._logger = logging.getLogger(
                f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
        return self._logger

    def set_log_level(self, level: int) -> None:
        """Set the logging level for this instance.

        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        self.logger.setLevel(level)

"""Logging mixin utilities for Cadence.

Provides `Loggable`, a base class that initializes a class-scoped logger
named `<module>.<ClassName>` for consistent, structured logging across the
codebase.
"""

import logging
import os


class Loggable:
    """Mixin providing a class-scoped logger.

    Subclass to get `self.logger` automatically configured to the fully
    qualified class name.
    """

    def __init__(self):
        """Initialize the logger for the subclass instance."""
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        if os.environ.get("CADENCE_DEBUG", "False") == "True":
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

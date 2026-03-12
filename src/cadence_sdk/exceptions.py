"""Base exception for all Cadence domain errors.

CadenceException is an abstract base class. All domain-specific exceptions
must inherit from it and implement error_category.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class CadenceException(ABC, Exception):
    """Abstract base exception for all Cadence errors.

    Do not raise CadenceException directly. Use specific subclasses
    (AuthenticationError, ValidationError, etc.) instead.
    """

    @property
    @abstractmethod
    def error_category(self) -> str:
        """Category of the error for grouping and logging."""
        ...

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize Cadence exception.

        Args:
            message: Human-readable error message
            code: Error code for programmatic handling
            status_code: HTTP status code
            field: Field name if this is a validation error
            details: Additional error context
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.field = field
        self.details = details or {}
        super().__init__(message)

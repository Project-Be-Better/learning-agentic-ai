"""
Custom exception classes for the Agent Framework.

Provides specialized exception types for security, validation, and runtime errors.
"""


class AgentException(Exception):
    """Base exception for all agent-related errors."""

    pass


class SecurityError(AgentException):
    """Raised when Intent Gate rejects a request due to security violation."""

    pass


class TamperingError(SecurityError):
    """Raised when capsule signature verification fails."""

    pass


class ExpirationError(SecurityError):
    """Raised when intent capsule has expired."""

    pass


class ConstraintViolationError(SecurityError):
    """Raised when capsule constraints are violated."""

    pass


class ValidationError(AgentException):
    """Raised when state validation fails."""

    pass


class MissingFieldError(ValidationError):
    """Raised when required field is missing in state."""

    pass

"""
Centralized exception handling with HTTP status codes.

Defines:
- Base API Exception
- Standard error responses
- Common HTTP exceptions
- Custom business logic exceptions
"""

from typing import Any, Optional

from fastapi import HTTPException, status


class APIError(HTTPException):
    """Base exception for API errors with structured response."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": details or {},
                }
            },
        )


# Standard HTTP exceptions
class BadRequestError(APIError):
    """400 - Invalid request parameters"""

    def __init__(
        self, message: str = "Invalid request", details: dict[str, Any] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="bad_request",
            message=message,
            details=details,
        )


class UnauthorizedError(APIError):
    """401 - Authentication required"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="unauthorized",
            message=message,
        )


class ForbiddenError(APIError):
    """403 - Insufficient permissions"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="forbidden",
            message=message,
        )


class NotFoundError(APIError):
    """404 - Resource not found"""

    def __init__(self, resource: str = "resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="not_found",
            message=f"{resource} not found",
        )


class RateLimitError(APIError):
    """429 - Rate limit exceeded"""

    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="rate_limit_exceeded",
            message="Too many requests",
            details={"retry_after": retry_after},
        )


# Business logic exceptions
class InsufficientCreditsError(APIError):
    """402 - Not enough credits"""

    def __init__(self, balance: int, required: int):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="insufficient_credits",
            message="Insufficient credits",
            details={"balance": balance, "required": required},
        )


class ServiceTimeoutError(APIError):
    """504 - Service timeout"""

    def __init__(self, service: str, timeout: int):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            error_code="service_timeout",
            message=f"{service} service timed out",
            details={"timeout_seconds": timeout},
        )
def log_and_raise_http_exception(logger, error_class, *args, log_message=None, **kwargs):
    """
    Logs an error message and raises an HTTP exception.
    
    Args:
        logger: The logger instance to use for logging
        error_class: The APIError subclass to instantiate
        *args: Positional arguments to pass to the error_class constructor
        log_message: Optional custom message to log (defaults to error class message)
        **kwargs: Keyword arguments to pass to the error_class constructor
    
    Raises:
        APIError: An instance of the specified error_class
    """
    exception = error_class(*args, **kwargs)
    message = log_message or exception.detail["error"]["message"]
    logger.error(f"HTTP {exception.status_code}: {message}")
    raise exception

        )

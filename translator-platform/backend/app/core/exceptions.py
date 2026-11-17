"""
Custom Application Exceptions

Defines all custom exceptions used throughout the application.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


# ============================================
# Authentication & Authorization Exceptions
# ============================================


class InvalidCredentialsException(AppException):
    """Raised when login credentials are invalid."""

    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredException(AppException):
    """Raised when JWT token has expired."""

    def __init__(self, detail: str = "Token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="TOKEN_EXPIRED",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenException(AppException):
    """Raised when JWT token is invalid or malformed."""

    def __init__(self, detail: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="INVALID_TOKEN",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InsufficientPermissionsException(AppException):
    """Raised when user lacks required permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="INSUFFICIENT_PERMISSIONS",
        )


class UserNotFoundException(AppException):
    """Raised when user is not found."""

    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="USER_NOT_FOUND",
        )


class UserAlreadyExistsException(AppException):
    """Raised when attempting to create a user that already exists."""

    def __init__(self, detail: str = "User with this email already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="USER_ALREADY_EXISTS",
        )


# ============================================
# Ticket Exceptions
# ============================================


class TicketNotFoundException(AppException):
    """Raised when ticket is not found."""

    def __init__(self, detail: str = "Ticket not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="TICKET_NOT_FOUND",
        )


class TicketStatusException(AppException):
    """Raised when ticket status transition is invalid."""

    def __init__(self, detail: str = "Invalid ticket status transition"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_TICKET_STATUS",
        )


class TicketAlreadyAssignedException(AppException):
    """Raised when ticket is already assigned."""

    def __init__(self, detail: str = "Ticket already assigned to a room agent"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="TICKET_ALREADY_ASSIGNED",
        )


# ============================================
# Room Exceptions
# ============================================


class RoomNotFoundException(AppException):
    """Raised when room is not found."""

    def __init__(self, detail: str = "Room not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="ROOM_NOT_FOUND",
        )


class RoomAccessDeniedException(AppException):
    """Raised when user tries to access unauthorized room."""

    def __init__(self, detail: str = "Access denied to this room"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="ROOM_ACCESS_DENIED",
        )


class RoomFullException(AppException):
    """Raised when room has reached maximum capacity."""

    def __init__(self, detail: str = "Room has reached maximum capacity"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="ROOM_FULL",
        )


# ============================================
# Glossary Exceptions
# ============================================


class GlossaryNotFoundException(AppException):
    """Raised when glossary/domain is not found."""

    def __init__(self, detail: str = "Glossary not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="GLOSSARY_NOT_FOUND",
        )


class InvalidGlossaryFileException(AppException):
    """Raised when uploaded glossary file is invalid."""

    def __init__(self, detail: str = "Invalid glossary file format"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_GLOSSARY_FILE",
        )


class GlossaryImportException(AppException):
    """Raised when glossary import fails."""

    def __init__(self, detail: str = "Failed to import glossary"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="GLOSSARY_IMPORT_FAILED",
        )


# ============================================
# Translation Exceptions
# ============================================


class TranslationException(AppException):
    """Raised when translation fails."""

    def __init__(self, detail: str = "Translation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="TRANSLATION_FAILED",
        )


class UnsupportedLanguagePairException(AppException):
    """Raised when language pair is not supported."""

    def __init__(self, detail: str = "Unsupported language pair"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="UNSUPPORTED_LANGUAGE_PAIR",
        )


class ModelUnavailableException(AppException):
    """Raised when translation model is unavailable."""

    def __init__(self, detail: str = "Translation model unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="MODEL_UNAVAILABLE",
        )


class TranslationTimeoutException(AppException):
    """Raised when translation request times out."""

    def __init__(self, detail: str = "Translation request timed out"):
        super().__init__(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=detail,
            error_code="TRANSLATION_TIMEOUT",
        )


# ============================================
# WebSocket Exceptions
# ============================================


class WebSocketAuthException(AppException):
    """Raised when WebSocket authentication fails."""

    def __init__(self, detail: str = "WebSocket authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="WS_AUTH_FAILED",
        )


class WebSocketRoomException(AppException):
    """Raised when WebSocket room operation fails."""

    def __init__(self, detail: str = "WebSocket room operation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="WS_ROOM_ERROR",
        )


# ============================================
# General Exceptions
# ============================================


class ValidationException(AppException):
    """Raised when request validation fails."""

    def __init__(self, detail: str = "Validation failed", errors: Optional[list] = None):
        error_detail = detail
        if errors:
            error_detail = {"message": detail, "errors": errors}
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_detail,
            error_code="VALIDATION_ERROR",
        )


class ResourceNotFoundException(AppException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail or f"{resource} not found",
            error_code=f"{resource.upper()}_NOT_FOUND",
        )


class ServiceUnavailableException(AppException):
    """Raised when a required service is unavailable."""

    def __init__(self, service: str, detail: Optional[str] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail or f"{service} is currently unavailable",
            error_code=f"{service.upper()}_UNAVAILABLE",
        )


class RateLimitExceededException(AppException):
    """Raised when rate limit is exceeded."""

    def __ __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED",
        )
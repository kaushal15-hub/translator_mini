"""
Security Utilities

Provides password hashing, JWT token creation/validation, and authentication utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from uuid import uuid4

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import SecretStr

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid4())})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid4())})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate an access token.

    Args:
        token: JWT access token

    Returns:
        Decoded payload if valid access token, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a refresh token.

    Args:
        token: JWT refresh token

    Returns:
        Decoded payload if valid refresh token, None otherwise
    """
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None


def create_token_pair(user_id: str, email: str, role: str) -> Dict[str, str]:
    """
    Create access and refresh token pair for a user.

    Args:
        user_id: User ID
        email: User email
        role: User role

    Returns:
        Dictionary with access_token and refresh_token
    """
    token_data = {"sub": user_id, "email": email, "role": role}
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }


class TokenData:
    """Token data container."""

    def __init__(
        self,
        user_id: str,
        email: str,
        role: str,
        exp: Optional[datetime] = None,
        jti: Optional[str] = None,
    ):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.exp = exp
        self.jti = jti

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "TokenData":
        """Create TokenData from decoded JWT payload."""
        return cls(
            user_id=payload.get("sub", ""),
            email=payload.get("email", ""),
            role=payload.get("role", ""),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            if payload.get("exp")
            else None,
            jti=payload.get("jti"),
        )


def get_token_expiry_minutes() -> int:
    """Get access token expiry in minutes."""
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES


def get_refresh_token_expiry_days() -> int:
    """Get refresh token expiry in days."""
    return settings.REFRESH_TOKEN_EXPIRE_DAYS
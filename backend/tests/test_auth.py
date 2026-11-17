"""
Authentication Tests

Tests for user registration, login, token refresh, and password change.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
    create_token_pair,
)
from app.models.user import User, Role, UserRole, UserStatus


class TestSecurity:
    """Test security utilities."""

    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "secure_password_123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_token_creation_and_decoding(self):
        """Test access token creation and decoding."""
        data = {"sub": "user-id", "email": "test@example.com", "role": "user"}

        access_token = create_access_token(data)
        decoded = decode_access_token(access_token)

        assert decoded is not None
        assert decoded["sub"] == "user-id"
        assert decoded["email"] == "test@example.com"
        assert decoded["role"] == "user"
        assert decoded["type"] == "access"
        assert "exp" in decoded
        assert "jti" in decoded

    def test_refresh_token_creation_and_decoding(self):
        """Test refresh token creation and decoding."""
        data = {"sub": "user-id", "email": "test@example.com", "role": "user"}

        refresh_token = create_refresh_token(data)
        decoded = decode_refresh_token(refresh_token)

        assert decoded is not None
        assert decoded["sub"] == "user-id"
        assert decoded["type"] == "refresh"

    def test_token_type_validation(self):
        """Test that access tokens are rejected by refresh decoder."""
        data = {"sub": "user-id"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        assert decode_access_token(access_token) is not None
        assert decode_refresh_token(access_token) is None

        assert decode_refresh_token(refresh_token) is not None
        assert decode_access_token(refresh_token) is None

    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected."""
        assert decode_access_token("invalid.token.string") is None
        assert decode_refresh_token("invalid.token.string") is None
        assert decode_access_token("") is None

    def test_token_pair_creation(self):
        """Test token pair creation."""
        tokens = create_token_pair(
            user_id="user-id",
            email="test@example.com",
            role="user"
        )

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

        access_decoded = decode_access_token(tokens["access_token"])
        refresh_decoded = decode_refresh_token(tokens["refresh_token"])

        assert access_decoded["sub"] == "user-id"
        assert refresh_decoded["sub"] == "user-id"


class TestUserModel:
    """Test User model properties."""

    def test_user_roles_property(self):
        """Test user role names property."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hash",
            full_name="Test User",
        )
        user.roles = [
            Role(name="user", display_name="User"),
            Role(name="admin", display_name="Admin"),
        ]

        assert user.role_names == ["user", "admin"]

    def test_has_role(self):
        """Test has_role method."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hash",
            full_name="Test User",
        )
        user.roles = [Role(name="user", display_name="User")]

        assert user.has_role("user")
        assert not user.has_role("admin")

    def test_is_admin(self):
        """Test is_admin property."""
        # Regular user
        user = User(
            id=uuid4(),
            email="user@example.com",
            hashed_password="hash",
            full_name="Regular User",
        )
        user.roles = [Role(name="user", display_name="User")]
        assert not user.is_admin()

        # Admin user
        admin = User(
            id=uuid4(),
            email="admin@example.com",
            hashed_password="hash",
            full_name="Admin User",
        )
        admin.roles = [Role(name="admin", display_name="Admin")]
        assert admin.is_admin()

        # Superuser
        superuser = User(
            id=uuid4(),
            email="super@example.com",
            hashed_password="hash",
            full_name="Super User",
        )
        superuser.is_superuser = True
        assert superuser.is_admin()

    def test_is_room_agent(self):
        """Test is_room_agent property."""
        user = User(
            id=uuid4(),
            email="agent@example.com",
            hashed_password="hash",
            full_name="Room Agent",
        )
        user.roles = [Role(name="room_agent", display_name="Room Agent")]
        assert user.is_room_agent()

        # Admin is also room agent
        admin = User(
            id=uuid4(),
            email="admin@example.com",
            hashed_password="hash",
            full_name="Admin",
        )
        admin.roles = [Role(name="admin", display_name="Admin")]
        assert admin.is_room_agent()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
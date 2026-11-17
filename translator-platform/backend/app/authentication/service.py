"""
Authentication Service

Business logic for user authentication, registration, and token management.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID
from hashlib import sha256

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    decode_refresh_token,
    get_refresh_token_expiry_days,
)
from app.core.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserNotFoundException,
    InvalidTokenException,
)
from app.models.user import User, Role, RefreshToken, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserAdminUpdate, RegisterRequest


class AuthService:
    """Authentication service for user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate a user with email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Authenticated user

        Raises:
            InvalidCredentialsException: If credentials are invalid
        """
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == email.lower())
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise InvalidCredentialsException()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()

        if user.status != UserStatus.ACTIVE:
            raise InvalidCredentialsException("Account is not active")

        return user

    async def register_user(self, user_data: RegisterRequest) -> User:
        """
        Register a new user.

        Args:
            user_data: Registration data

        Returns:
            Created user

        Raises:
            UserAlreadyExistsException: If email already exists
        """
        # Check if user exists
        stmt = select(User).where(User.email == user_data.email.lower())
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise UserAlreadyExistsException()

        # Get default user role
        stmt = select(Role).where(Role.name == UserRole.USER)
        result = await self.db.execute(stmt)
        user_role = result.scalar_one_or_none()

        # Create user
        user = User(
            email=user_data.email.lower(),
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
            preferred_language=user_data.preferred_language,
            status=UserStatus.ACTIVE,
        )

        if user_role:
            user.roles.append(user_role)

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def create_user_admin(self, user_data: UserCreate) -> User:
        """
        Create a user as admin (with role assignment).

        Args:
            user_data: User creation data

        Returns:
            Created user
        """
        # Check if user exists
        stmt = select(User).where(User.email == user_data.email.lower())
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise UserAlreadyExistsException()

        user = User(
            email=user_data.email.lower(),
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
            preferred_language=user_data.preferred_language,
            status=UserStatus.ACTIVE,
        )

        # Assign roles
        if user_data.role_names:
            stmt = select(Role).where(Role.name.in_(user_data.role_names))
            result = await self.db.execute(stmt)
            roles = result.scalars().all()
            user.roles.extend(roles)

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID with roles loaded."""
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email with roles loaded."""
        stmt = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.email == email.lower())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        """
        Update user profile.

        Args:
            user_id: User ID
            user_data: Update data

        Returns:
            Updated user
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_user_admin(self, user_id: UUID, user_data: UserAdminUpdate) -> User:
        """
        Update user as admin (including roles and status).

        Args:
            user_id: User ID
            user_data: Admin update data

        Returns:
            Updated user
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        update_data = user_data.model_dump(exclude_unset=True)

        # Handle roles separately
        if "roles" in update_data:
            role_names = update_data.pop("roles")
            stmt = select(Role).where(Role.name.in_(role_names))
            result = await self.db.execute(stmt)
            user.roles = list(result.scalars().all())

        # Handle status
        if "status" in update_data:
            user.status = UserStatus(update_data.pop("status"))

        # Apply remaining updates
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            True if successful
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsException("Current password is incorrect")

        user.hashed_password = get_password_hash(new_password)
        await self.db.flush()
        return True

    async def create_tokens(self, user: User) -> dict:
        """
        Create access and refresh tokens for user.

        Args:
            user: Authenticated user

        Returns:
            Token pair dictionary
        """
        # Determine primary role
        primary_role = user.roles[0].name if user.roles else UserRole.USER

        tokens = create_token_pair(
            user_id=str(user.id),
            email=user.email,
            role=primary_role,
        )

        # Store refresh token
        refresh_token = tokens["refresh_token"]
        token_hash = sha256(refresh_token.encode()).hexdigest()
        jti = decode_refresh_token(refresh_token).get("jti")

        rt = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            jti=jti,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=get_refresh_token_expiry_days()),
        )
        self.db.add(rt)

        # Update last login
        user.last_login = datetime.now(timezone.utc)

        await self.db.flush()
        return tokens

    async def refresh_tokens(self, refresh_token: str) -> dict:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token pair

        Raises:
            InvalidTokenException: If refresh token is invalid
        """
        payload = decode_refresh_token(refresh_token)
        if not payload:
            raise InvalidTokenException("Invalid refresh token")

        jti = payload.get("jti")
        user_id = payload.get("sub")

        # Verify token in database
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.jti == jti,
                RefreshToken.user_id == UUID(user_id),
                RefreshToken.revoked == False,
            )
        )
        result = await self.db.execute(stmt)
        stored_token = result.scalar_one_or_none()

        if not stored_token:
            raise InvalidTokenException("Refresh token not found or revoked")

        if stored_token.expires_at < datetime.now(timezone.utc):
            raise InvalidTokenException("Refresh token expired")

        # Mark old token as used
        stored_token.revoked = True
        stored_token.used_at = datetime.now(timezone.utc)

        # Get user
        user = await self.get_user_by_id(UUID(user_id))
        if not user or user.status != UserStatus.ACTIVE:
            raise InvalidTokenException("User not found or inactive")

        # Create new tokens
        tokens = await self.create_tokens(user)
        return tokens

    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        Revoke a refresh token (logout).

        Args:
            refresh_token: Refresh token to revoke

        Returns:
            True if revoked
        """
        payload = decode_refresh_token(refresh_token)
        if not payload:
            return False

        jti = payload.get("jti")
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        result = await self.db.execute(stmt)
        token = result.scalar_one_or_none()

        if token:
            token.revoked = True
            token.used_at = datetime.now(timezone.utc)
            await self.db.flush()
            return True

        return False

    async def revoke_all_user_tokens(self, user_id: UUID) -> int:
        """
        Revoke all refresh tokens for a user.

        Args:
            user_id: User ID

        Returns:
            Number of tokens revoked
        """
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
            )
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()

        count = 0
        for token in tokens:
            token.revoked = True
            token.used_at = datetime.now(timezone.utc)
            count += 1

        await self.db.flush()
        return count

    async def list_users(
        self, page: int = 1, size: int = 20, search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """
        List users with pagination and search.

        Args:
            page: Page number (1-indexed)
            size: Page size
            search: Search query for email or name

        Returns:
            Tuple of (users, total_count)
        """
        stmt = select(User).options(selectinload(User.roles))

        if search:
            search_term = f"%{search.lower()}%"
            stmt = stmt.where(
                (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
            )

        # Count total
        count_stmt = select(User.id)
        if search:
            search_term = f"%{search.lower()}%"
            count_stmt = count_stmt.where(
                (User.email.ilike(search_term)) | (User.full_name.ilike(search_term))
            )
        total_result = await self.db.execute(count_stmt)
        total = len(total_result.scalars().all())

        # Apply pagination
        stmt = stmt.offset((page - 1) * size).limit(size).order_by(User.created_at.desc())
        result = await self.db.execute(stmt)
        users = result.scalars().all()

        return list(users), total

    async def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user (soft delete by setting status to inactive).

        Args:
            user_id: User ID

        Returns:
            True if deleted
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException()

        user.status = UserStatus.INACTIVE
        await self.db.flush()
        return True
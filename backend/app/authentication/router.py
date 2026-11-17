"""
Authentication Router

API endpoints for authentication, registration, and token management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token, TokenData
from app.core.exceptions import InvalidTokenException, InsufficientPermissionsException
from app.authentication.service import AuthService
from app.schemas.user import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    UserResponse,
    UserCreate,
    UserUpdate,
    UserAdminUpdate,
    UserPasswordChange,
    Token,
    MessageResponse,
    UserListResponse,
    RoleResponse,
    RoleCreate,
    RoleUpdate,
)
from app.models.user import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)


# ============================================
# Dependencies
# ============================================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current user

    Raises:
        InvalidTokenException: If token is invalid or expired
    """
    if not credentials:
        raise InvalidTokenException("Missing authorization header")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise InvalidTokenException("Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenException("Invalid token payload")

    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(UUID(user_id))

    if not user or user.status.value != "active":
        raise InvalidTokenException("User not found or inactive")

    return UserResponse.model_validate(user)


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Get current active user (alias for clarity)."""
    return current_user


async def get_current_admin(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user and verify admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if admin

    Raises:
        InsufficientPermissionsException: If user is not admin
    """
    if not current_user.is_superuser and UserRole.ADMIN not in [r.name for r in current_user.roles]:
        raise InsufficientPermissionsException("Admin access required")
    return current_user


async def get_current_room_agent(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user and verify room agent role.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if room agent or admin

    Raises:
        InsufficientPermissionsException: If user is not room agent
    """
    user_roles = [r.name for r in current_user.roles]
    if (
        not current_user.is_superuser
        and UserRole.ADMIN not in user_roles
        and UserRole.ROOM_AGENT not in user_roles
    ):
        raise InsufficientPermissionsException("Room agent access required")
    return current_user


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)


# ============================================
# Authentication Endpoints
# ============================================


@router.post("/login", response_model=Token, summary="User login")
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Authenticate user and return access/refresh tokens.

    Args:
        login_data: Login credentials
        auth_service: Authentication service

    Returns:
        Access and refresh tokens
    """
    user = await auth_service.authenticate_user(login_data.email, login_data.password)
    tokens = await auth_service.create_tokens(user)
    return Token(**tokens)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="User registration")
async def register(
    register_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Register a new user.

    Args:
        register_data: Registration data
        auth_service: Authentication service

    Returns:
        Created user
    """
    user = await auth_service.register_user(register_data)
    return UserResponse.model_validate(user)


@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Refresh access token using refresh token.

    Args:
        refresh_data: Refresh token request
        auth_service: Authentication service

    Returns:
        New access and refresh tokens
    """
    tokens = await auth_service.refresh_tokens(refresh_data.refresh_token)
    return Token(**tokens)


@router.post("/logout", response_model=MessageResponse, summary="User logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Logout user by revoking refresh token.

    Args:
        refresh_data: Refresh token to revoke
        auth_service: Authentication service

    Returns:
        Success message
    """
    await auth_service.revoke_refresh_token(refresh_data.refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.post("/logout-all", response_model=MessageResponse, summary="Logout from all devices")
async def logout_all(
    current_user: UserResponse = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Revoke all refresh tokens for current user.

    Args:
        current_user: Current authenticated user
        auth_service: Authentication service

    Returns:
        Success message
    """
    count = await auth_service.revoke_all_user_tokens(UUID(current_user.id))
    return MessageResponse(message=f"Logged out from {count} device(s)")


# ============================================
# User Profile Endpoints
# ============================================


@router.get("/me", response_model=UserResponse, summary="Get current user profile")
async def get_profile(
    current_user: UserResponse = Depends(get_current_active_user),
) -> UserResponse:
    """
    Get current user's profile.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user profile
    """
    return current_user


@router.put("/me", response_model=UserResponse, summary="Update current user profile")
async def update_profile(
    user_data: UserUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Update current user's profile.

    Args:
        user_data: Profile update data
        current_user: Current authenticated user
        auth_service: Authentication service

    Returns:
        Updated user profile
    """
    user = await auth_service.update_user(UUID(current_user.id), user_data)
    return UserResponse.model_validate(user)


@router.put("/me/password", response_model=MessageResponse, summary="Change password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: UserResponse = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Change current user's password.

    Args:
        password_data: Password change data
        current_user: Current authenticated user
        auth_service: Authentication service

    Returns:
        Success message
    """
    await auth_service.change_password(
        UUID(current_user.id), password_data.current_password, password_data.new_password
    )
    return MessageResponse(message="Password changed successfully")


# ============================================
# Admin User Management Endpoints
# ============================================


@router.get("/users", response_model=UserListResponse, summary="List all users (admin)")
async def list_users(
    page: int = 1,
    size: int = 20,
    search: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_admin),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserListResponse:
    """
    List all users with pagination and search (admin only).

    Args:
        page: Page number
        size: Page size
        search: Search query
        current_user: Current admin user
        auth_service: Authentication service

    Returns:
        Paginated user list
    """
    users, total = await auth_service.list_users(page, size, search)
    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/users/{user_id}", response_model=UserResponse, summary="Get user by ID (admin)")
async def get_user(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_admin),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID
        current_user: Current admin user
        auth_service: Authentication service

    Returns:
        User profile
    """
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create user (admin)")
async def create_user(
    user_data: UserCreate,
    current_user: UserResponse = Depends(get_current_admin),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Create a new user (admin only).

    Args:
        user_data: User creation data
        current_user: Current admin user
        auth_service: Authentication service

    Returns:
        Created user
    """
    user = await auth_service.create_user_admin(user_data)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse, summary="Update user (admin)")
async def update_user(
    user_id: UUID,
    user_data: UserAdminUpdate,
    current_user: UserResponse = Depends(get_current_admin),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Update user (admin only).

    Args:
        user_id: User ID
        user_data: Admin update data
        current_user: Current admin user
        auth_service: Authentication service

    Returns:
        Updated user
    """
    user = await auth_service.update_user_admin(user_id, user_data)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", response_model=MessageResponse, summary="Delete user (admin)")
async def delete_user(
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_admin),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """
    Delete/deactivate user (admin only).

    Args:
        user_id: User ID
        current_user: Current admin user
        auth_service: Authentication service

    Returns:
        Success message
    """
    if UUID(current_user.id) == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    await auth_service.delete_user(user_id)
    return MessageResponse(message="User deactivated successfully")


# ============================================
# Role Management Endpoints (Admin)
# ============================================


@router.get("/roles", response_model=list[RoleResponse], summary="List all roles")
async def list_roles(
    current_user: UserResponse = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[RoleResponse]:
    """
    List all roles (admin only).

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        List of roles
    """
    from sqlalchemy import select
    from app.models.user import Role

    stmt = select(Role).order_by(Role.name)
    result = await db.execute(stmt)
    roles = result.scalars().all()
    return [RoleResponse.model_validate(r) for r in roles]


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED, summary="Create role")
async def create_role(
    role_data: RoleCreate,
    current_user: UserResponse = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    """
    Create a new role (admin only).

    Args:
        role_data: Role creation data
        current_user: Current admin user
        db: Database session

    Returns:
        Created role
    """
    from app.models.user import Role

    role = Role(**role_data.model_dump())
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return RoleResponse.model_validate(role)


@router.put("/roles/{role_id}", response_model=RoleResponse, summary="Update role")
async def update_role(
    role_id: UUID,
    role_data: RoleUpdate,
    current_user: UserResponse = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> RoleResponse:
    """
    Update a role (admin only).

    Args:
        role_id: Role ID
        role_data: Role update data
        current_user: Current admin user
        db: Database session

    Returns:
        Updated role
    """
    from sqlalchemy import select
    from app.models.user import Role
    from app.core.exceptions import ResourceNotFoundException

    stmt = select(Role).where(Role.id == role_id)
    result = await db.execute(stmt)
    role = result.scalar_one_or_none()

    if not role:
        raise ResourceNotFoundException("Role")

    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system role")

    update_data = role_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    await db.flush()
    await db.refresh(role)
    return RoleResponse.model_validate(role)
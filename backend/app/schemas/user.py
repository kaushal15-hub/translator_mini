"""
User Schemas

Pydantic models for user-related API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RoleBase(BaseModel):
    """Base role schema."""

    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class RoleCreate(RoleBase):
    """Schema for creating a role."""

    pass


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class RoleResponse(RoleBase):
    """Schema for role response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_system: bool
    created_at: datetime
    updated_at: datetime


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    preferred_language: str = Field(default="en", pattern="^(en|kn|hi|ml|ta)$")


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8, max_length=128)
    role_names: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    preferred_language: Optional[str] = Field(None, pattern="^(en|kn|hi|ml|ta)$")
    avatar_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Schema for password change."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserAdminUpdate(BaseModel):
    """Schema for admin user updates."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    preferred_language: Optional[str] = Field(None, pattern="^(en|kn|hi|ml|ta)$")
    status: Optional[str] = Field(None, pattern="^(active|inactive|suspended|pending_verification)$")
    is_superuser: Optional[bool] = None
    roles: Optional[List[str]] = None


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    avatar_url: Optional[str] = None
    status: str
    is_superuser: bool
    last_login: Optional[datetime] = None
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    roles: List[RoleResponse] = []


class UserListResponse(BaseModel):
    """Schema for paginated user list."""

    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""

    user_id: str
    email: str
    role: str
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str
    remember_me: bool = False


class RegisterRequest(BaseModel):
    """Registration request schema."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    preferred_language: str = Field(default="en", pattern="^(en|kn|hi|ml|ta)$")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
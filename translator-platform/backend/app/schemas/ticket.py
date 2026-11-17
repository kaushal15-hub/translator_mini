"""
Ticket and Room Schemas

Pydantic models for ticket, room, and message API requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TicketStatus(str, Enum):
    """Ticket status enumeration."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ASSIGNED = "assigned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TicketPriority(str, Enum):
    """Ticket priority enumeration."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ConversationDomain(str, Enum):
    """Conversation domain enumeration."""

    TECHNOLOGY = "technology"
    MEDICAL = "medical"
    GENERAL = "general"


class LanguageCode(str, Enum):
    """Supported language codes."""

    ENGLISH = "en"
    KANNADA = "kn"
    HINDI = "hi"
    MALAYALAM = "ml"
    TAMIL = "ta"


class TicketBase(BaseModel):
    """Base ticket schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    priority: TicketPriority = TicketPriority.NORMAL
    domain: ConversationDomain = ConversationDomain.GENERAL
    source_language: LanguageCode = LanguageCode.ENGLISH
    target_language: LanguageCode = LanguageCode.KANNADA


class TicketCreate(TicketBase):
    """Schema for creating a ticket."""

    pass


class TicketUpdate(BaseModel):
    """Schema for updating a ticket."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    domain: Optional[ConversationDomain] = None
    source_language: Optional[LanguageCode] = None
    target_language: Optional[LanguageCode] = None


class TicketAdminUpdate(BaseModel):
    """Schema for admin ticket updates."""

    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    domain: Optional[ConversationDomain] = None
    source_language: Optional[LanguageCode] = None
    target_language: Optional[LanguageCode] = None
    assigned_to_id: Optional[UUID] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class TicketResponse(TicketBase):
    """Schema for ticket response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: TicketStatus
    created_by_id: UUID
    assigned_to_id: Optional[UUID] = None
    room_id: Optional[UUID] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TicketDetailResponse(TicketResponse):
    """Detailed ticket response with related data."""

    creator_name: Optional[str] = None
    creator_email: Optional[str] = None
    assignee_name: Optional[str] = None
    assignee_email: Optional[str] = None
    room_name: Optional[str] = None


class TicketListResponse(BaseModel):
    """Schema for paginated ticket list."""

    tickets: List[TicketResponse]
    total: int
    page: int
    size: int
    pages: int


class RoomBase(BaseModel):
    """Base room schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    domain: ConversationDomain = ConversationDomain.GENERAL
    source_language: LanguageCode = LanguageCode.ENGLISH
    target_language: LanguageCode = LanguageCode.KANNADA
    max_participants: int = Field(default=2, ge=2, le=50)


class RoomCreate(RoomBase):
    """Schema for creating a room."""

    pass


class RoomUpdate(BaseModel):
    """Schema for updating a room."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    domain: Optional[ConversationDomain] = None
    source_language: Optional[LanguageCode] = None
    target_language: Optional[LanguageCode] = None
    max_participants: Optional[int] = Field(None, ge=2, le=50)
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


class RoomResponse(RoomBase):
    """Schema for room response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    settings: Dict[str, Any]
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None


class RoomDetailResponse(RoomResponse):
    """Detailed room response with members."""

    creator_name: Optional[str] = None
    member_count: int = 0
    members: List["RoomMemberResponse"] = []


class RoomMemberBase(BaseModel):
    """Base room member schema."""

    user_id: UUID
    role: str = Field(default="participant", pattern="^(participant|moderator|agent)$")
    permissions: Dict[str, Any] = Field(default_factory=dict)


class RoomMemberCreate(RoomMemberBase):
    """Schema for adding a room member."""

    pass


class RoomMemberUpdate(BaseModel):
    """Schema for updating a room member."""

    role: Optional[str] = Field(None, pattern="^(participant|moderator|agent)$")
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class RoomMemberResponse(RoomMemberBase):
    """Schema for room member response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    is_active: bool
    joined_at: datetime
    left_at: Optional[datetime] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_preferred_language: Optional[str] = None


class RoomListResponse(BaseModel):
    """Schema for paginated room list."""

    rooms: List[RoomResponse]
    total: int
    page: int
    size: int
    pages: int


class MessageBase(BaseModel):
    """Base message schema."""

    original_text: str = Field(..., min_length=1)
    original_language: LanguageCode
    domain: ConversationDomain


class MessageCreate(MessageBase):
    """Schema for creating a message."""

    room_id: UUID
    ticket_id: Optional[UUID] = None


class MessageUpdate(BaseModel):
    """Schema for updating a message (typically translation)."""

    translated_text: Optional[str] = None
    translated_language: Optional[LanguageCode] = None
    glossary_applied: Optional[bool] = None
    protected_terms: Optional[Dict[str, Any]] = None
    translation_metadata: Optional[Dict[str, Any]] = None
    delivery_status: Optional[str] = None


class MessageResponse(MessageBase):
    """Schema for message response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_id: UUID
    ticket_id: Optional[UUID] = None
    sender_id: UUID
    translated_text: Optional[str] = None
    translated_language: Optional[LanguageCode] = None
    glossary_applied: bool
    protected_terms: Optional[Dict[str, Any]] = None
    translation_metadata: Optional[Dict[str, Any]] = None
    delivery_status: str
    created_at: datetime
    updated_at: datetime


class MessageDetailResponse(MessageResponse):
    """Detailed message response with sender info."""

    sender_name: Optional[str] = None
    sender_preferred_language: Optional[str] = None


class MessageListResponse(BaseModel):
    """Schema for paginated message list."""

    messages: List[MessageResponse]
    total: int
    page: int
    size: int
    pages: int


class TranslationRequest(BaseModel):
    """Translation request schema."""

    text: str = Field(..., min_length=1, max_length=5000)
    source_language: LanguageCode
    target_language: LanguageCode
    domain: ConversationDomain = ConversationDomain.GENERAL
    context_messages: List[str] = Field(default_factory=list, max_length=4)
    glossary_id: Optional[UUID] = None


class TranslationResponse(BaseModel):
    """Translation response schema."""

    original_text: str
    translated_text: str
    source_language: LanguageCode
    target_language: LanguageCode
    domain: ConversationDomain
    protected_terms: Dict[str, str] = Field(default_factory=dict)
    translation_time_ms: float
    model_used: str
    glossary_applied: bool


# Forward reference resolution
RoomMemberResponse.model_rebuild()
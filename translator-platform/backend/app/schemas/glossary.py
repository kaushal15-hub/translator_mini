"""
Glossary Schemas

Pydantic models for glossary and terminology API requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class GlossaryDomain(str, Enum):
    """Glossary domain enumeration."""

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


class TermStatus(str, Enum):
    """Term status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class GlossaryBase(BaseModel):
    """Base glossary schema."""

    name: str = Field(..., min_length=1, max_length=200)
    domain: GlossaryDomain
    source_language: LanguageCode
    target_language: Optional[LanguageCode] = None
    description: Optional[str] = None
    version: str = Field(default="1.0", max_length=20)


class GlossaryCreate(GlossaryBase):
    """Schema for creating a glossary."""

    is_default: bool = False


class GlossaryUpdate(BaseModel):
    """Schema for updating a glossary."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class GlossaryResponse(GlossaryBase):
    """Schema for glossary response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_default: bool
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    term_count: int = 0


class GlossaryDetailResponse(GlossaryResponse):
    """Detailed glossary response with terms."""

    terms: List["GlossaryTermResponse"] = []
    creator_name: Optional[str] = None


class GlossaryListResponse(BaseModel):
    """Schema for paginated glossary list."""

    glossaries: List[GlossaryResponse]
    total: int
    page: int
    size: int
    pages: int


class GlossaryTermBase(BaseModel):
    """Base glossary term schema."""

    original_term: str = Field(..., min_length=1, max_length=500)
    alternatives: List[str] = Field(default_factory=list)
    aliases: List[str] = Field(default_factory=list)
    source_language: LanguageCode
    target_language: Optional[LanguageCode] = None
    case_sensitive: bool = True
    preserve_original: bool = True
    priority: int = Field(default=10, ge=1, le=100)
    status: TermStatus = TermStatus.ACTIVE
    context: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GlossaryTermCreate(GlossaryTermBase):
    """Schema for creating a glossary term."""

    glossary_id: UUID


class GlossaryTermUpdate(BaseModel):
    """Schema for updating a glossary term."""

    original_term: Optional[str] = Field(None, min_length=1, max_length=500)
    alternatives: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    target_language: Optional[LanguageCode] = None
    case_sensitive: Optional[bool] = None
    preserve_original: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    status: Optional[TermStatus] = None
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GlossaryTermResponse(GlossaryTermBase):
    """Schema for glossary term response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    glossary_id: UUID
    created_at: datetime
    updated_at: datetime


class GlossaryTermListResponse(BaseModel):
    """Schema for paginated glossary term list."""

    terms: List[GlossaryTermResponse]
    total: int
    page: int
    size: int
    pages: int


class GlossaryImportRequest(BaseModel):
    """Schema for glossary import request."""

    glossary_id: Optional[UUID] = None
    domain: GlossaryDomain
    source_language: LanguageCode
    target_language: Optional[LanguageCode] = None
    name: Optional[str] = None
    overwrite: bool = False


class GlossaryImportResponse(BaseModel):
    """Schema for glossary import response."""

    success: bool
    message: str
    glossary_id: Optional[UUID] = None
    total_rows: int = 0
    successful_rows: int = 0
    failed_rows: int = 0
    errors: Optional[List[Dict[str, Any]]] = None


class GlossaryTermCSVRow(BaseModel):
    """Schema for CSV glossary term row."""

    original_term: str
    alternatives: str = ""  # Comma-separated
    aliases: str = ""  # Comma-separated
    domain: str
    source_language: str
    target_language: str = ""
    case_sensitive: str = "true"
    preserve_original: str = "true"
    priority: str = "10"
    active: str = "true"

    def to_term_create(self) -> GlossaryTermCreate:
        """Convert CSV row to term create schema."""
        return GlossaryTermCreate(
            original_term=self.original_term.strip(),
            alternatives=[a.strip() for a in self.alternatives.split(",") if a.strip()],
            aliases=[a.strip() for a in self.aliases.split(",") if a.strip()],
            source_language=LanguageCode(self.source_language),
            target_language=LanguageCode(self.target_language) if self.target_language else None,
            case_sensitive=self.case_sensitive.lower() == "true",
            preserve_original=self.preserve_original.lower() == "true",
            priority=int(self.priority),
            status=TermStatus.ACTIVE if self.active.lower() == "true" else TermStatus.INACTIVE,
            glossary_id=UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
        )


# Forward reference resolution
GlossaryTermResponse.model_rebuild()
GlossaryDetailResponse.model_rebuild()
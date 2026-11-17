"""
Glossary Router

API endpoints for glossary and terminology management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.authentication.router import get_current_active_user, get_current_admin
from app.glossary.service import GlossaryService
from app.schemas.glossary import (
    GlossaryCreate,
    GlossaryUpdate,
    GlossaryResponse,
    GlossaryDetailResponse,
    GlossaryListResponse,
    GlossaryTermCreate,
    GlossaryTermUpdate,
    GlossaryTermResponse,
    GlossaryTermListResponse,
    GlossaryImportRequest,
    GlossaryImportResponse,
    GlossaryDomain,
    TermStatus,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/glossaries", tags=["Glossaries"])


def get_glossary_service(db: AsyncSession = Depends(get_db)) -> GlossaryService:
    """Get glossary service instance."""
    return GlossaryService(db)


# ============================================
# Glossary Endpoints
# ============================================


@router.post("", response_model=GlossaryResponse, status_code=status.HTTP_201_CREATED, summary="Create glossary")
async def create_glossary(
    glossary_data: GlossaryCreate,
    current_user: UserResponse = Depends(get_current_admin),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryResponse:
    """
    Create a new glossary (admin only).

    Args:
        glossary_data: Glossary creation data
        current_user: Current admin user
        glossary_service: Glossary service

    Returns:
        Created glossary
    """
    glossary = await glossary_service.create_glossary(UUID(current_user.id), glossary_data)
    return GlossaryResponse.model_validate(glossary)


@router.get("", response_model=GlossaryListResponse, summary="List glossaries")
async def list_glossaries(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    domain_filter: Optional[GlossaryDomain] = None,
    active_only: bool = True,
    current_user: UserResponse = Depends(get_current_active_user),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryListResponse:
    """
    List glossaries with pagination.

    Args:
        page: Page number
        size: Page size
        domain_filter: Optional domain filter
        active_only: Only show active glossaries
        current_user: Current authenticated user
        glossary_service: Glossary service

    Returns:
        Paginated glossary list
    """
    glossaries, total = await glossary_service.list_glossaries(
        page, size, domain_filter, active_only
    )
    return GlossaryListResponse(
        glossaries=[GlossaryResponse.model_validate(g) for g in glossaries],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/default", response_model=Optional[GlossaryResponse], summary="Get default glossary for domain")
async def get_default_glossary(
    domain: GlossaryDomain,
    source_language: str,
    target_language: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_active_user),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> Optional[GlossaryResponse]:
    """
    Get default glossary for a domain and language pair.

    Args:
        domain: Conversation domain
        source_language: Source language code
        target_language: Optional target language code
        current_user: Current authenticated user
        glossary_service: Glossary service

    Returns:
        Default glossary or None
    """
    glossary = await glossary_service.get_default_glossary(domain, source_language, target_language)
    if glossary:
        return GlossaryResponse.model_validate(glossary)
    return None


@router.get("/{glossary_id}", response_model=GlossaryDetailResponse, summary="Get glossary details")
async def get_glossary(
    glossary_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryDetailResponse:
    """
    Get glossary details with terms.

    Args:
        glossary_id: Glossary ID
        current_user: Current authenticated user
        glossary_service: Glossary service

    Returns:
        Glossary details with terms
    """
    glossary = await glossary_service.get_glossary_detail(glossary_id)
    return GlossaryDetailResponse.model_validate(glossary)


@router.put("/{glossary_id}", response_model=GlossaryResponse, summary="Update glossary")
async def update_glossary(
    glossary_id: UUID,
    glossary_data: GlossaryUpdate,
    current_user: UserResponse = Depends(get_current_admin),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryResponse:
    """
    Update a glossary (admin only).

    Args:
        glossary_id: Glossary ID
        glossary_data: Update data
        current_user: Current admin user
        glossary_service: Glossary service

    Returns:
        Updated glossary
    """
    glossary = await glossary_service.update_glossary(glossary_id, glossary_data)
    return GlossaryResponse.model_validate(glossary)


@router.delete("/{glossary_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete glossary")
async def delete_glossary(
    glossary_id: UUID,
    current_user: UserResponse = Depends(get_current_admin),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> None:
    """
    Delete a glossary (admin only).

    Args:
        glossary_id: Glossary ID
        current_user: Current admin user
        glossary_service: Glossary service
    """
    await glossary_service.delete_glossary(glossary_id)


# ============================================
# Glossary Term Endpoints
# ============================================


@router.post("/{glossary_id}/terms", response_model=GlossaryTermResponse, status_code=status.HTTP_201_CREATED, summary="Create glossary term")
async def create_term(
    glossary_id: UUID,
    term_data: GlossaryTermCreate,
    current_user: UserResponse = Depends(get_current_admin),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTermResponse:
    """
    Create a new glossary term (admin only).

    Args:
        glossary_id: Glossary ID
        term_data: Term creation data
        current_user: Current admin user
        glossary_service: Glossary service

    Returns:
        Created term
    """
    term_data.glossary_id = glossary_id
    term = await glossary_service.create_term(term_data)
    return GlossaryTermResponse.model_validate(term)


@router.get("/{glossary_id}/terms", response_model=GlossaryTermListResponse, summary="List glossary terms")
async def list_terms(
    glossary_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    status_filter: Optional[TermStatus] = None,
    search: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_active_user),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTermListResponse:
    """
    List terms for a glossary.

    Args:
        glossary_id: Glossary ID
        page: Page number
        size: Page size
        status_filter: Optional status filter
        search: Search query
        current_user: Current authenticated user
        glossary_service: Glossary service

    Returns:
        Paginated term list
    """
    terms, total = await glossary_service.list_terms(
        glossary_id, page, size, status_filter, search
    )
    return GlossaryTermListResponse(
        terms=[GlossaryTermResponse.model_validate(t) for t in terms],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{glossary_id}/terms/{term_id}", response_model=GlossaryTermResponse, summary="Get term details")
async def get_term(
    glossary_id: UUID,
    term_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTermResponse:
    """
    Get term details.

    Args:
        glossary_id: Glossary ID
        term_id: Term ID
        current_user: Current authenticated user
        glossary_service: Glossary service

    Returns:
        Term details
    """
    term = await glossary_service.get_term_by_id(term_id)
    if not term or term.glossary_id != glossary_id:
        raise HTTPException(status_code=404, detail="Term not found")
    return GlossaryTermResponse.model_validate(term)


@router.put("/{glossary_id}/terms/{term_id}", response_model=GlossaryTermResponse, summary="Update glossary term")
async def update_term(
    glossary_id: UUID,
    term_id: UUID,
    term_data: GlossaryTermUpdate,
    current_user: UserResponse = Depends(get_current_admin),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryTermResponse:
    """
    Update a glossary term (admin only).

    Args:
        glossary_id: Glossary ID
        term_id: Term ID
        term_data: Update data
        current_user: Current admin user
        glossary_service: Glossary service

    Returns:
        Updated term
    """
    term = await glossary_service.get_term_by_id(term_id)
    if not term or term.glossary_id != glossary_id:
        raise HTTPException(status_code=404, detail="Term not found")

    term = await glossary_service.update_term(term_id, term_data)
    return GlossaryTermResponse.model_validate(term)


@router.delete("/{glossary_id}/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete glossary term")
async def delete_term(
    glossary_id: UUID,
    term_id: UUID,
    current_user: UserResponse = Depends(get_current_admin),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> None:
    """
    Delete a glossary term (admin only).

    Args:
        glossary_id: Glossary ID
        term_id: Term ID
        current_user: Current admin user
        glossary_service: Glossary service
    """
    await glossary_service.delete_term(term_id)


# ============================================
# Glossary Import Endpoint
# ============================================


@router.post("/import", response_model=GlossaryImportResponse, summary="Import glossary from file")
async def import_glossary(
    file: UploadFile = File(...),
    domain: GlossaryDomain = Query(...),
    source_language: str = Query(...),
    target_language: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    overwrite: bool = Query(False),
    glossary_id: Optional[UUID] = Query(None),
    current_user: UserResponse = Depends(get_current_admin),
    glossary_service: GlossaryService = Depends(get_glossary_service),
) -> GlossaryImportResponse:
    """
    Import glossary from CSV or JSON file (admin only).

    Args:
        file: Upload file (CSV or JSON)
        domain: Glossary domain
        source_language: Source language code
        target_language: Optional target language code
        name: Optional glossary name
        overwrite: Whether to overwrite existing terms
        glossary_id: Optional existing glossary ID
        current_user: Current admin user
        glossary_service: Glossary service

    Returns:
        Import result
    """
    # Validate file format
    filename = file.filename or ""
    if filename.endswith(".csv"):
        file_format = "csv"
    elif filename.endswith(".json"):
        file_format = "json"
    else:
        raise HTTPException(status_code=400, detail="File must be CSV or JSON")

    # Read file content
    content = await file.read()

    # Create import request
    import_request = GlossaryImportRequest(
        glossary_id=glossary_id,
        domain=domain,
        source_language=source_language,
        target_language=target_language,
        name=name,
        overwrite=overwrite,
    )

    # Import
    result = await glossary_service.import_glossary(
        UUID(current_user.id), content, file_format, import_request
    )

    return result
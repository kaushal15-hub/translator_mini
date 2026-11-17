"""
Glossary Service

Business logic for glossary and terminology management.
"""

import csv
import json
from datetime import datetime
from io import StringIO
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    GlossaryNotFoundException,
    InvalidGlossaryFileException,
    GlossaryImportException,
)
from app.models.glossary import (
    Glossary,
    GlossaryTerm,
    GlossaryImportLog,
    GlossaryDomain,
    TermStatus,
)
from app.models.user import User
from app.schemas.glossary import (
    GlossaryCreate,
    GlossaryUpdate,
    GlossaryTermCreate,
    GlossaryTermUpdate,
    GlossaryImportRequest,
    GlossaryImportResponse,
)


class GlossaryService:
    """Glossary management service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # Glossary CRUD Operations
    # ============================================

    async def create_glossary(self, creator_id: UUID, glossary_data: GlossaryCreate) -> Glossary:
        """
        Create a new glossary.

        Args:
            creator_id: ID of user creating the glossary
            glossary_data: Glossary creation data

        Returns:
            Created glossary
        """
        # If setting as default, unset other defaults for same domain/lang
        if glossary_data.is_default:
            await self._unset_default_glossary(
                glossary_data.domain,
                glossary_data.source_language,
                glossary_data.target_language,
            )

        glossary = Glossary(
            **glossary_data.model_dump(),
            created_by_id=creator_id,
        )
        self.db.add(glossary)
        await self.db.flush()
        await self.db.refresh(glossary)
        return glossary

    async def get_glossary_by_id(self, glossary_id: UUID) -> Optional[Glossary]:
        """Get glossary by ID with terms loaded."""
        stmt = (
            select(Glossary)
            .options(selectinload(Glossary.terms))
            .where(Glossary.id == glossary_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_glossary_detail(self, glossary_id: UUID) -> Glossary:
        """Get glossary by ID or raise exception."""
        glossary = await self.get_glossary_by_id(glossary_id)
        if not glossary:
            raise GlossaryNotFoundException()
        return glossary

    async def get_default_glossary(
        self, domain: GlossaryDomain, source_lang: str, target_lang: Optional[str] = None
    ) -> Optional[Glossary]:
        """Get default glossary for domain and language pair."""
        stmt = select(Glossary).where(
            Glossary.domain == domain,
            Glossary.source_language == source_lang,
            Glossary.target_language == target_lang,
            Glossary.is_default == True,
            Glossary.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_glossary(self, glossary_id: UUID, glossary_data: GlossaryUpdate) -> Glossary:
        """
        Update a glossary.

        Args:
            glossary_id: Glossary ID
            glossary_data: Update data

        Returns:
            Updated glossary
        """
        glossary = await self.get_glossary_detail(glossary_id)

        update_data = glossary_data.model_dump(exclude_unset=True)

        # Handle is_default
        if "is_default" in update_data and update_data["is_default"]:
            await self._unset_default_glossary(
                glossary.domain,
                glossary.source_language,
                glossary.target_language,
            )

        for field, value in update_data.items():
            setattr(glossary, field, value)

        await self.db.flush()
        await self.db.refresh(glossary)
        return glossary

    async def delete_glossary(self, glossary_id: UUID) -> bool:
        """
        Delete a glossary (soft delete by setting inactive).

        Args:
            glossary_id: Glossary ID

        Returns:
            True if deleted
        """
        glossary = await self.get_glossary_detail(glossary_id)
        glossary.is_active = False
        await self.db.flush()
        return True

    async def list_glossaries(
        self,
        page: int = 1,
        size: int = 20,
        domain_filter: Optional[GlossaryDomain] = None,
        active_only: bool = True,
    ) -> Tuple[List[Glossary], int]:
        """
        List glossaries with pagination.

        Args:
            page: Page number
            size: Page size
            domain_filter: Optional domain filter
            active_only: Only show active glossaries

        Returns:
            Tuple of (glossaries, total_count)
        """
        stmt = select(Glossary).options(selectinload(Glossary.terms))

        if active_only:
            stmt = stmt.where(Glossary.is_active == True)
        if domain_filter:
            stmt = stmt.where(Glossary.domain == domain_filter)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(Glossary.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        glossaries = result.scalars().all()

        return list(glossaries), total

    async def _unset_default_glossary(
        self, domain: GlossaryDomain, source_lang: str, target_lang: Optional[str]
    ) -> None:
        """Unset default flag for other glossaries with same domain/lang."""
        stmt = select(Glossary).where(
            Glossary.domain == domain,
            Glossary.source_language == source_lang,
            Glossary.target_language == target_lang,
            Glossary.is_default == True,
        )
        result = await self.db.execute(stmt)
        glossaries = result.scalars().all()
        for g in glossaries:
            g.is_default = False

    # ============================================
    # Glossary Term Operations
    # ============================================

    async def create_term(self, term_data: GlossaryTermCreate) -> GlossaryTerm:
        """
        Create a new glossary term.

        Args:
            term_data: Term creation data

        Returns:
            Created term
        """
        # Verify glossary exists
        await self.get_glossary_detail(term_data.glossary_id)

        term = GlossaryTerm(**term_data.model_dump())
        self.db.add(term)
        await self.db.flush()
        await self.db.refresh(term)
        return term

    async def get_term_by_id(self, term_id: UUID) -> Optional[GlossaryTerm]:
        """Get term by ID."""
        stmt = select(GlossaryTerm).where(GlossaryTerm.id == term_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_term(self, term_id: UUID, term_data: GlossaryTermUpdate) -> GlossaryTerm:
        """
        Update a glossary term.

        Args:
            term_id: Term ID
            term_data: Update data

        Returns:
            Updated term
        """
        term = await self.get_term_by_id(term_id)
        if not term:
            from app.core.exceptions import ResourceNotFoundException
            raise ResourceNotFoundException("GlossaryTerm")

        update_data = term_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(term, field, value)

        await self.db.flush()
        await self.db.refresh(term)
        return term

    async def delete_term(self, term_id: UUID) -> bool:
        """
        Delete a glossary term.

        Args:
            term_id: Term ID

        Returns:
            True if deleted
        """
        term = await self.get_term_by_id(term_id)
        if not term:
            from app.core.exceptions import ResourceNotFoundException
            raise ResourceNotFoundException("GlossaryTerm")

        await self.db.delete(term)
        await self.db.flush()
        return True

    async def list_terms(
        self,
        glossary_id: UUID,
        page: int = 1,
        size: int = 50,
        status_filter: Optional[TermStatus] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[GlossaryTerm], int]:
        """
        List terms for a glossary.

        Args:
            glossary_id: Glossary ID
            page: Page number
            size: Page size
            status_filter: Optional status filter
            search: Search query for term

        Returns:
            Tuple of (terms, total_count)
        """
        stmt = select(GlossaryTerm).where(GlossaryTerm.glossary_id == glossary_id)

        if status_filter:
            stmt = stmt.where(GlossaryTerm.status == status_filter)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    GlossaryTerm.original_term.ilike(search_term),
                    GlossaryTerm.context.ilike(search_term),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(GlossaryTerm.priority.desc(), GlossaryTerm.original_term).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        terms = result.scalars().all()

        return list(terms), total

    # ============================================
    # Glossary Import
    # ============================================

    async def import_glossary(
        self,
        creator_id: UUID,
        file_content: bytes,
        file_format: str,
        import_request: GlossaryImportRequest,
    ) -> GlossaryImportResponse:
        """
        Import glossary from CSV or JSON file.

        Args:
            creator_id: User ID importing the glossary
            file_content: File content bytes
            file_format: 'csv' or 'json'
            import_request: Import configuration

        Returns:
            Import result
        """
        # Get or create glossary
        glossary = None
        if import_request.glossary_id:
            glossary = await self.get_glossary_detail(import_request.glossary_id)
        else:
            # Create new glossary
            glossary_name = import_request.name or f"Imported {import_request.domain.value} glossary"
            glossary = await self.create_glossary(
                creator_id,
                GlossaryCreate(
                    name=glossary_name,
                    domain=import_request.domain,
                    source_language=import_request.source_language,
                    target_language=import_request.target_language,
                    description=f"Imported from {file_format.upper()} file",
                ),
            )

        # Parse file
        if file_format == "csv":
            terms_data = self._parse_csv(file_content)
        elif file_format == "json":
            terms_data = self._parse_json(file_content)
        else:
            raise InvalidGlossaryFileException(f"Unsupported format: {file_format}")

        # Process terms
        successful = 0
        failed = 0
        errors = []

        for idx, term_data in enumerate(terms_data):
            try:
                # Check for existing term if not overwriting
                if not import_request.overwrite:
                    existing = await self._find_existing_term(
                        glossary.id, term_data.original_term
                    )
                    if existing:
                        errors.append({
                            "row": idx + 1,
                            "term": term_data.original_term,
                            "error": "Term already exists (use overwrite to replace)",
                        })
                        failed += 1
                        continue

                # Create or update term
                term_create = GlossaryTermCreate(
                    **term_data.model_dump(),
                    glossary_id=glossary.id,
                )
                await self.create_term(term_create)
                successful += 1

            except Exception as e:
                errors.append({
                    "row": idx + 1,
                    "term": term_data.original_term,
                    "error": str(e),
                })
                failed += 1

        # Log import
        import_log = GlossaryImportLog(
            glossary_id=glossary.id,
            filename=f"import_{datetime.utcnow().isoformat()}.{file_format}",
            file_format=file_format,
            total_rows=len(terms_data),
            successful_rows=successful,
            failed_rows=failed,
            errors=errors if errors else None,
            imported_by_id=creator_id,
        )
        self.db.add(import_log)
        await self.db.flush()

        return GlossaryImportResponse(
            success=failed == 0,
            message=f"Imported {successful} terms, {failed} failed",
            glossary_id=glossary.id,
            total_rows=len(terms_data),
            successful_rows=successful,
            failed_rows=failed,
            errors=errors if errors else None,
        )

    def _parse_csv(self, content: bytes) -> List[GlossaryTermCreate]:
        """Parse CSV file content."""
        try:
            text = content.decode("utf-8")
            reader = csv.DictReader(StringIO(text))
            terms = []

            for row in reader:
                # Map CSV columns to term fields
                term = GlossaryTermCreate(
                    original_term=row.get("original_term", "").strip(),
                    alternatives=[a.strip() for a in row.get("alternatives", "").split(",") if a.strip()],
                    aliases=[a.strip() for a in row.get("aliases", "").split(",") if a.strip()],
                    source_language=row.get("source_language", "en"),
                    target_language=row.get("target_language") or None,
                    case_sensitive=row.get("case_sensitive", "true").lower() == "true",
                    preserve_original=row.get("preserve_original", "true").lower() == "true",
                    priority=int(row.get("priority", "10")),
                    status=TermStatus.ACTIVE if row.get("active", "true").lower() == "true" else TermStatus.INACTIVE,
                    context=row.get("context") or None,
                    glossary_id=UUID("00000000-0000-0000-0000-000000000000"),  # Will be set later
                )
                terms.append(term)

            return terms
        except Exception as e:
            raise InvalidGlossaryFileException(f"Failed to parse CSV: {str(e)}")

    def _parse_json(self, content: bytes) -> List[GlossaryTermCreate]:
        """Parse JSON file content."""
        try:
            data = json.loads(content.decode("utf-8"))
            terms = []

            for item in data:
                term = GlossaryTermCreate(
                    original_term=item.get("original_term", "").strip(),
                    alternatives=item.get("alternatives", []),
                    aliases=item.get("aliases", []),
                    source_language=item.get("source_language", "en"),
                    target_language=item.get("target_language") or None,
                    case_sensitive=item.get("case_sensitive", True),
                    preserve_original=item.get("preserve_original", True),
                    priority=item.get("priority", 10),
                    status=TermStatus(item.get("status", "active")),
                    context=item.get("context") or None,
                    metadata=item.get("metadata", {}),
                    glossary_id=UUID("00000000-0000-0000-0000-000000000000"),
                )
                terms.append(term)

            return terms
        except Exception as e:
            raise InvalidGlossaryFileException(f"Failed to parse JSON: {str(e)}")

    async def _find_existing_term(self, glossary_id: UUID, original_term: str) -> Optional[GlossaryTerm]:
        """Find existing term by original_term in glossary."""
        stmt = select(GlossaryTerm).where(
            GlossaryTerm.glossary_id == glossary_id,
            GlossaryTerm.original_term == original_term,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ============================================
    # Terminology Lookup for Translation
    # ============================================

    async def get_active_terms_for_domain(
        self, domain: GlossaryDomain, source_lang: str, target_lang: Optional[str] = None
    ) -> List[GlossaryTerm]:
        """
        Get all active terms for a domain and language pair.

        Args:
            domain: Conversation domain
            source_lang: Source language code
            target_lang: Optional target language code

        Returns:
            List of active glossary terms
        """
        # Get default glossary for domain
        glossary = await self.get_default_glossary(domain, source_lang, target_lang)
        if not glossary:
            return []

        stmt = select(GlossaryTerm).where(
            GlossaryTerm.glossary_id == glossary.id,
            GlossaryTerm.status == TermStatus.ACTIVE,
            GlossaryTerm.source_language == source_lang,
            or_(
                GlossaryTerm.target_language == target_lang,
                GlossaryTerm.target_language.is_(None),
            ),
        ).order_by(GlossaryTerm.priority.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
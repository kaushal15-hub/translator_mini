"""
Glossary Package

Exports glossary components.
"""

from app.glossary.service import GlossaryService
from app.glossary.router import router as glossary_router

__all__ = ["GlossaryService", "glossary_router"]
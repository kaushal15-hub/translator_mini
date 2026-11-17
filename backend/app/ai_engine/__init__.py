"""
AI Engine Package

Exports AI/ML components.
"""

from app.ai_engine.terminology.matcher import (
    TerminologyMatcher,
    get_terminology_matcher,
    rebuild_matcher,
    MatchedTerm,
    ProtectionResult,
)
from app.ai_engine.translation.service import TranslationService, get_translation_service
from app.ai_engine.context.manager import ConversationContextManager, get_context_manager

__all__ = [
    "TerminologyMatcher",
    "get_terminology_matcher",
    "rebuild_matcher",
    "MatchedTerm",
    "ProtectionResult",
    "TranslationService",
    "get_translation_service",
    "ConversationContextManager",
    "get_context_manager",
]
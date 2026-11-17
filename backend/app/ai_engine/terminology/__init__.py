"""
Terminology Package

Exports terminology matching components.
"""

from app.ai_engine.terminology.matcher import (
    TerminologyMatcher,
    get_terminology_matcher,
    rebuild_matcher,
    MatchedTerm,
    ProtectionResult,
)

__all__ = [
    "TerminologyMatcher",
    "get_terminology_matcher",
    "rebuild_matcher",
    "MatchedTerm",
    "ProtectionResult",
]
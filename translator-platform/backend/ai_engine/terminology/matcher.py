"""
Aho-Corasick Terminology Matcher

Efficient multi-pattern matching for terminology protection during translation.
"""

import ahocorasick
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from uuid import uuid4

from app.models.glossary import GlossaryTerm, TermStatus


@dataclass
class MatchedTerm:
    """Represents a matched protected term in text."""

    original_text: str
    matched_variant: str
    term_id: str
    start_pos: int
    end_pos: int
    priority: int
    case_sensitive: bool
    preserve_original: bool
    target_replacement: Optional[str] = None


@dataclass
class ProtectionResult:
    """Result of terminology protection process."""

    protected_text: str
    placeholder_map: Dict[str, str]  # placeholder -> original term
    matched_terms: List[MatchedTerm]


class TerminologyMatcher:
    """
    Aho-Corasick based terminology matcher for efficient multi-pattern matching.

    Features:
    - Longest match priority
    - Case sensitivity handling
    - Overlapping term resolution
    - Placeholder collision prevention
    - Alias and alternative spelling support
    """

    def __init__(self):
        self._automaton: Optional[ahocorasick.Automaton] = None
        self._term_data: Dict[str, GlossaryTerm] = {}  # term_id -> GlossaryTerm
        self._pattern_to_term: Dict[str, str] = {}  # pattern -> term_id
        self._built = False

    def build(self, terms: List[GlossaryTerm]) -> None:
        """
        Build the Aho-Corasick automaton from glossary terms.

        Args:
            terms: List of active glossary terms
        """
        self._automaton = ahocorasick.Automaton()
        self._term_data = {}
        self._pattern_to_term = {}

        for term in terms:
            if term.status != TermStatus.ACTIVE:
                continue

            term_id = str(term.id)
            self._term_data[term_id] = term

            # Add original term
            self._add_pattern(term.original_term, term_id)

            # Add alternatives
            for alt in term.alternatives:
                self._add_pattern(alt, term_id)

            # Add aliases
            for alias in term.aliases:
                self._add_pattern(alias, term_id)

        # Build the automaton
        self._automaton.make_automaton()
        self._built = True

    def _add_pattern(self, pattern: str, term_id: str) -> None:
        """Add a pattern to the automaton."""
        if not pattern:
            return

        # Store pattern mapping
        self._pattern_to_term[pattern] = term_id

        # Add to automaton with term_id as value
        # We store (term_id, pattern) to identify which pattern matched
        self._automaton.add_word(pattern, (term_id, pattern))

    def find_matches(self, text: str) -> List[MatchedTerm]:
        """
        Find all protected term matches in text.

        Args:
            text: Input text to search

        Returns:
            List of matched terms sorted by position and priority
        """
        if not self._built or not self._automaton:
            return []

        matches = []

        for end_pos, (term_id, matched_pattern) in self._automaton.iter(text):
            term = self._term_data.get(term_id)
            if not term:
                continue

            start_pos = end_pos - len(matched_pattern) + 1
            matched_text = text[start_pos : end_pos + 1]

            # Verify case sensitivity
            if term.case_sensitive and matched_text != matched_pattern:
                continue

            # Get target replacement if available
            target_replacement = None
            if term.target_language and term.preserve_original:
                target_replacement = term.original_term

            match = MatchedTerm(
                original_text=matched_text,
                matched_variant=matched_pattern,
                term_id=term_id,
                start_pos=start_pos,
                end_pos=end_pos + 1,
                priority=term.priority,
                case_sensitive=term.case_sensitive,
                preserve_original=term.preserve_original,
                target_replacement=target_replacement,
            )
            matches.append(match)

        # Resolve overlaps - keep longest match, then highest priority
        return self._resolve_overlaps(matches)

    def _resolve_overlaps(self, matches: List[MatchedTerm]) -> List[MatchedTerm]:
        """
        Resolve overlapping matches using longest-match-first, then priority.

        Args:
            matches: List of all matches

        Returns:
            List of non-overlapping matches
        """
        if not matches:
            return []

        # Sort by start position, then by length (descending), then priority (descending)
        matches.sort(key=lambda m: (m.start_pos, -(m.end_pos - m.start_pos), -m.priority))

        resolved = []
        last_end = -1

        for match in matches:
            # Check if this match overlaps with the last accepted match
            if match.start_pos >= last_end:
                resolved.append(match)
                last_end = match.end_pos
            # If overlapping, the longer/higher priority one was already accepted due to sorting

        return resolved

    def protect_text(self, text: str) -> ProtectionResult:
        """
        Protect terminology in text by replacing with placeholders.

        Args:
            text: Input text

        Returns:
            ProtectionResult with protected text and placeholder map
        """
        matches = self.find_matches(text)

        if not matches:
            return ProtectionResult(
                protected_text=text,
                placeholder_map={},
                matched_terms=[],
            )

        # Build protected text with placeholders
        protected_parts = []
        last_end = 0
        placeholder_map = {}

        for match in matches:
            # Add text before match
            protected_parts.append(text[last_end : match.start_pos])

            # Generate unique placeholder
            placeholder = f"__TERM_{match.term_id[:8]}_{uuid4().hex[:8]}__"
            protected_parts.append(placeholder)

            # Store mapping
            placeholder_map[placeholder] = match.original_text

            last_end = match.end_pos

        # Add remaining text
        protected_parts.append(text[last_end:])

        protected_text = "".join(protected_parts)

        return ProtectionResult(
            protected_text=protected_text,
            placeholder_map=placeholder_map,
            matched_terms=matches,
        )

    def restore_text(self, protected_text: str, placeholder_map: Dict[str, str]) -> str:
        """
        Restore protected terms from placeholders.

        Args:
            protected_text: Text with placeholders
            placeholder_map: Mapping of placeholder -> original term

        Returns:
            Restored text
        """
        restored = protected_text
        for placeholder, original in placeholder_map.items():
            restored = restored.replace(placeholder, original)
        return restored

    def validate_restoration(
        self, original_text: str, restored_text: str, matched_terms: List[MatchedTerm]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all protected terms were correctly restored.

        Args:
            original_text: Original input text
            restored_text: Text after translation and restoration
            matched_terms: List of matched terms

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check each matched term
        for match in matched_terms:
            if match.preserve_original:
                if match.original_text not in restored_text:
                    errors.append(
                        f"Protected term '{match.original_text}' not found in restored text"
                    )

        # Check for leftover placeholders
        import re
        placeholders = re.findall(r"__TERM_[A-F0-9]+_[A-F0-9]+__", restored_text)
        if placeholders:
            errors.append(f"Unrestored placeholders found: {placeholders}")

        return len(errors) == 0, errors


# Global matcher instance for reuse
_matcher_instance: Optional[TerminologyMatcher] = None


def get_terminology_matcher() -> TerminologyMatcher:
    """Get or create global terminology matcher instance."""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = TerminologyMatcher()
    return _matcher_instance


def rebuild_matcher(terms: List[GlossaryTerm]) -> TerminologyMatcher:
    """Rebuild the global matcher with new terms."""
    global _matcher_instance
    _matcher_instance = TerminologyMatcher()
    _matcher_instance.build(terms)
    return _matcher_instance
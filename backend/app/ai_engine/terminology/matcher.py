"""
Aho-Corasick Terminology Matcher

Pure Python implementation with optional C extension support.
"""

try:
    import ahocorasick
    HAS_AHOCORASICK = True
except ImportError:
    HAS_AHOCORASICK = False

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
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


class PureAhoCorasick:
    """
    Pure Python Aho-Corasick automaton.
    Drop-in replacement for ahocorasick.Automaton for basic use cases.
    """
    
    def __init__(self):
        self._root = {}
        self._fail = {}
        self._output = {}
        self._built = False
    
    def add_word(self, pattern: str, value: Any = None) -> None:
        """Add a pattern to the trie."""
        if value is None:
            value = pattern
        node = self._root
        for char in pattern:
            if char not in node:
                node[char] = {}
            node = node[char]
        if "_out" not in node:
            node["_out"] = []
        node["_out"].append((pattern, value))
    
    def make_automaton(self) -> None:
        """Build failure links using BFS."""
        from collections import deque
        
        queue = deque()
        
        # Initialize root's children
        for char, child in self._root.items():
            if isinstance(child, dict):
                self._fail[id(child)] = self._root
                queue.append(child)
        
        # BFS to build failure links
        while queue:
            current = queue.popleft()
            
            for char, child in current.items():
                if char == "_out" or not isinstance(child, dict):
                    continue
                queue.append(child)
                
                # Find failure link
                fail = self._fail.get(id(current), self._root)
                while fail is not self._root and char not in fail:
                    fail = self._fail.get(id(fail), self._root)
                
                self._fail[id(child)] = fail.get(char, self._root)
                
                # Merge outputs
                if "_out" in self._fail[id(child)]:
                    if "_out" not in child:
                        child["_out"] = []
                    child["_out"].extend(self._fail[id(child)]["_out"])
        
        self._built = True
    
    def iter(self, text: str):
        """Iterate over matches in text."""
        if not self._built:
            self.make_automaton()
        
        node = self._root
        for i, char in enumerate(text):
            while node is not self._root and char not in node:
                node = self._fail.get(id(node), self._root)
            
            if char in node:
                node = node[char]
            else:
                node = self._root
            
            if "_out" in node:
                for pattern, value in node["_out"]:
                    start = i - len(pattern) + 1
                    yield (i, (value, pattern))


class TerminologyMatcher:
    """
    Terminology matcher with optional C extension support.
    Falls back to pure Python if ahocorasick is not available.
    """

    def __init__(self):
        if HAS_AHOCORASICK:
            self._automaton = ahocorasick.Automaton()
        else:
            self._automaton = PureAhoCorasick()
        self._term_data: Dict[str, GlossaryTerm] = {}
        self._pattern_to_term: Dict[str, str] = {}
        self._built = False

    def build(self, terms: List[GlossaryTerm]) -> None:
        """Build the automaton from glossary terms."""
        self._automaton = ahocorasick.Automaton() if HAS_AHOCORASICK else PureAhoCorasick()
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
        self._pattern_to_term[pattern] = term_id
        self._automaton.add_word(pattern, (term_id, pattern))

    def find_matches(self, text: str) -> List[MatchedTerm]:
        """Find all protected term matches in text."""
        if not self._built:
            return []

        matches = []

        if HAS_AHOCORASICK:
            for end_pos, (term_id, matched_pattern) in self._automaton.iter(text):
                term = self._term_data.get(term_id)
                if not term:
                    continue

                start_pos = end_pos - len(matched_pattern) + 1
                matched_text = text[start_pos : end_pos + 1]

                # Verify case sensitivity
                if term.case_sensitive and matched_text != matched_pattern:
                    continue

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
        else:
            # Pure Python implementation
            for end_pos, (term_id, matched_pattern) in self._automaton.iter(text):
                term = self._term_data.get(term_id)
                if not term:
                    continue

                start_pos = end_pos - len(matched_pattern) + 1
                matched_text = text[start_pos : end_pos + 1]

                if term.case_sensitive and matched_text != matched_pattern:
                    continue

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
        """Resolve overlapping matches using longest-match-first, then priority."""
        if not matches:
            return []

        # Sort by start position, then by length (descending), then priority (descending)
        matches.sort(key=lambda m: (m.start_pos, -(m.end_pos - m.start_pos), -m.priority))

        resolved = []
        last_end = -1

        for match in matches:
            if match.start_pos >= last_end:
                resolved.append(match)
                last_end = match.end_pos

        return resolved

    def protect_text(self, text: str) -> ProtectionResult:
        """Protect terminology in text by replacing with placeholders."""
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
            protected_parts.append(text[last_end : match.start_pos])

            placeholder = f"__TERM_{match.term_id[:8]}_{uuid4().hex[:8]}__"
            protected_parts.append(placeholder)

            placeholder_map[placeholder] = match.original_text
            last_end = match.end_pos

        protected_parts.append(text[last_end:])

        protected_text = "".join(protected_parts)

        return ProtectionResult(
            protected_text=protected_text,
            placeholder_map=placeholder_map,
            matched_terms=matches,
        )

    def restore_text(self, protected_text: str, placeholder_map: Dict[str, str]) -> str:
        """Restore protected terms from placeholders."""
        restored = protected_text
        for placeholder, original in placeholder_map.items():
            restored = restored.replace(placeholder, original)
        return restored

    def validate_restoration(
        self, original_text: str, restored_text: str, matched_terms: List[MatchedTerm]
    ) -> Tuple[bool, List[str]]:
        """Validate that all protected terms were correctly restored."""
        errors = []

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
"""
Tests for Terminology Matcher (Aho-Corasick)

Tests protected term preservation, alias matching, case sensitivity,
overlapping terminology, longest-match priority, placeholder restoration,
punctuation preservation, and multiple protected terms in one sentence.
"""

import pytest
from uuid import uuid4

from app.ai_engine.terminology.matcher import (
    TerminologyMatcher,
    MatchedTerm,
    ProtectionResult,
)
from app.models.glossary import GlossaryTerm, TermStatus, LanguageCode


def create_test_term(
    original_term: str,
    alternatives: list = None,
    aliases: list = None,
    case_sensitive: bool = True,
    preserve_original: bool = True,
    priority: int = 10,
    source_language: str = "en",
    target_language: str = None,
) -> GlossaryTerm:
    """Helper to create a test glossary term."""
    return GlossaryTerm(
        id=uuid4(),
        glossary_id=uuid4(),
        original_term=original_term,
        alternatives=alternatives or [],
        aliases=aliases or [],
        source_language=LanguageCode(source_language),
        target_language=LanguageCode(target_language) if target_language else None,
        case_sensitive=case_sensitive,
        preserve_original=preserve_original,
        priority=priority,
        status=TermStatus.ACTIVE,
        context=None,
        metadata={},
    )


class TestTerminologyMatcher:
    """Test suite for TerminologyMatcher."""

    def setup_method(self):
        """Set up fresh matcher for each test."""
        self.matcher = TerminologyMatcher()

    def test_basic_term_protection(self):
        """Test basic term protection with single term."""
        terms = [create_test_term("Python", preserve_original=True)]
        self.matcher.build(terms)

        text = "I love Python programming"
        result = self.matcher.protect_text(text)

        assert isinstance(result, ProtectionResult)
        assert len(result.matched_terms) == 1
        assert result.matched_terms[0].original_text == "Python"
        assert "__TERM_" in result.protected_text
        assert "Python" not in result.protected_text

    def test_multiple_terms_protection(self):
        """Test protection of multiple different terms."""
        terms = [
            create_test_term("Python"),
            create_test_term("Machine Learning"),
            create_test_term("API"),
        ]
        self.matcher.build(terms)

        text = "Python is used for Machine Learning via API"
        result = self.matcher.protect_text(text)

        assert len(result.matched_terms) == 3
        assert len(result.placeholder_map) == 3
        for term_text in ["Python", "Machine Learning", "API"]:
            assert term_text not in result.protected_text
            assert any(term_text in v for v in result.placeholder_map.values())

    def test_case_sensitive_matching(self):
        """Test case sensitive term matching."""
        terms = [create_test_term("Python", case_sensitive=True)]
        self.matcher.build(terms)

        # Exact case should match
        result = self.matcher.protect_text("I love Python")
        assert len(result.matched_terms) == 1

        # Different case should not match
        result = self.matcher.protect_text("I love python")
        assert len(result.matched_terms) == 0

    def test_case_insensitive_matching(self):
        """Test case insensitive term matching."""
        terms = [create_test_term("Python", case_sensitive=False)]
        self.matcher.build(terms)

        result = self.matcher.protect_text("I love python")
        assert len(result.matched_terms) == 1
        assert result.matched_terms[0].original_text == "python"

    def test_alias_matching(self):
        """Test alias matching."""
        terms = [create_test_term("Python", aliases=["Py", "Python3"])]
        self.matcher.build(terms)

        # Original term
        result = self.matcher.protect_text("I love Python")
        assert len(result.matched_terms) == 1

        # Alias
        result = self.matcher.protect_text("I love Py")
        assert len(result.matched_terms) == 1
        assert result.matched_terms[0].original_text == "Py"

        result = self.matcher.protect_text("I love Python3")
        assert len(result.matched_terms) == 1
        assert result.matched_terms[0].original_text == "Python3"

    def test_alternatives_matching(self):
        """Test alternative spelling matching."""
        terms = [create_test_term("Machine Learning", alternatives=["ML", "M.L."])]
        self.matcher.build(terms)

        result = self.matcher.protect_text("ML is great")
        assert len(result.matched_terms) == 1
        assert result.matched_terms[0].matched_variant == "ML"

    def test_longest_match_priority(self):
        """Test longest match wins for overlapping terms."""
        terms = [
            create_test_term("Machine Learning", priority=10),
            create_test_term("Machine", priority=5),
        ]
        self.matcher.build(terms)

        text = "Machine Learning is cool"
        result = self.matcher.protect_text(text)

        # Should match "Machine Learning" not "Machine"
        assert len(result.matched_terms) == 1
        assert result.matched_terms[0].original_text == "Machine Learning"

    def test_priority_for_same_length(self):
        """Test priority wins for same length overlapping terms."""
        terms = [
            create_test_term("AI Model", priority=5),
            create_test_term("AI Model", priority=10),  # Higher priority
        ]
        self.matcher.build(terms)

        text = "AI Model is deployed"
        result = self.matcher.protect_text(text)

        # Should have only one match (deduplicated)
        assert len(result.matched_terms) == 1
        assert result.matched_terms[0].priority == 10

    def test_overlapping_terms_resolution(self):
        """Test resolution of overlapping terms."""
        terms = [
            create_test_term("Deep Learning", priority=10),
            create_test_term("Learning Rate", priority=5),
        ]
        self.matcher.build(terms)

        text = "Deep Learning Rate is important"
        result = self.matcher.protect_text(text)

        # Should match "Deep Learning" (starts first, longer)
        matched_texts = [m.original_text for m in result.matched_terms]
        assert "Deep Learning" in matched_texts

    def test_punctuation_preservation(self):
        """Test punctuation is preserved around protected terms."""
        terms = [create_test_term("Python")]
        self.matcher.build(terms)

        text = "I love Python, it's great! (Python)"
        result = self.matcher.protect_text(text)

        # Punctuation should remain
        assert "," in result.protected_text
        assert "!" in result.protected_text
        assert "(" in result.protected_text
        assert ")" in result.protected_text

    def test_placeholder_restoration(self):
        """Test restoration of protected terms after translation."""
        terms = [create_test_term("Python"), create_test_term("API")]
        self.matcher.build(terms)

        text = "Python uses API"
        result = self.matcher.protect_text(text)

        # Simulate translation (placeholder stays same)
        translated = result.protected_text

        # Restore
        restored = self.matcher.restore_text(translated, result.placeholder_map)

        assert "Python" in restored
        assert "API" in restored
        assert "__TERM_" not in restored

    def test_restoration_validation(self):
        """Test validation of restoration."""
        terms = [create_test_term("Python", preserve_original=True)]
        self.matcher.build(terms)

        text = "Python is awesome"
        result = self.matcher.protect_text(text)

        # Good restoration
        restored = self.matcher.restore_text(result.protected_text, result.placeholder_map)
        is_valid, errors = self.matcher.validate_restoration(text, restored, result.matched_terms)
        assert is_valid
        assert len(errors) == 0

        # Bad restoration (term missing)
        bad_restored = "is awesome"
        is_valid, errors = self.matcher.validate_restoration(text, bad_restored, result.matched_terms)
        assert not is_valid
        assert len(errors) > 0

    def test_unmatched_text_preserved(self):
        """Test that unmatched text is not silently removed."""
        terms = [create_test_term("Python")]
        self.matcher.build(terms)

        text = "Hello Python world"
        result = self.matcher.protect_text(text)

        # "Hello" and "world" should remain
        assert "Hello" in result.protected_text
        assert "world" in result.protected_text

    def test_empty_text(self):
        """Test handling of empty text."""
        terms = [create_test_term("Python")]
        self.matcher.build(terms)

        result = self.matcher.protect_text("")
        assert result.protected_text == ""
        assert len(result.matched_terms) == 0
        assert len(result.placeholder_map) == 0

    def test_no_matches(self):
        """Test text with no protected terms."""
        terms = [create_test_term("Python")]
        self.matcher.build(terms)

        text = "Hello world"
        result = self.matcher.protect_text(text)

        assert result.protected_text == text
        assert len(result.matched_terms) == 0
        assert len(result.placeholder_map) == 0

    def test_placeholder_collision_prevention(self):
        """Test that placeholders don't collide."""
        terms = [
            create_test_term("Term1"),
            create_test_term("Term2"),
            create_test_term("Term3"),
        ]
        self.matcher.build(terms)

        text = "Term1 Term2 Term3"
        result = self.matcher.protect_text(text)

        # All placeholders should be unique
        placeholders = list(result.placeholder_map.keys())
        assert len(placeholders) == len(set(placeholders))

    def test_multiple_occurrences_same_term(self):
        """Test multiple occurrences of same term."""
        terms = [create_test_term("Python")]
        self.matcher.build(terms)

        text = "Python is Python and Python"
        result = self.matcher.protect_text(text)

        # Should match all three occurrences
        assert len(result.matched_terms) == 3
        assert len(result.placeholder_map) == 3

        # All should restore to Python
        restored = self.matcher.restore_text(result.protected_text, result.placeholder_map)
        assert restored.count("Python") == 3

    def test_mixed_languages(self):
        """Test terms with different source/target languages."""
        terms = [
            create_test_term("Python", source_language="en", target_language="kn"),
            create_test_term("ಕಂಪ್ಯೂಟರ್", source_language="kn", target_language="en"),
        ]
        self.matcher.build(terms)

        text = "Python and ಕಂಪ್ಯೂಟರ್"
        result = self.matcher.protect_text(text)

        assert len(result.matched_terms) == 2
        matched = {m.original_text for m in result.matched_terms}
        assert "Python" in matched
        assert "ಕಂಪ್ಯೂಟರ್" in matched

    def test_inactive_terms_ignored(self):
        """Test that inactive terms are not matched."""
        terms = [
            create_test_term("Python", priority=10),
            create_test_term("Java", status=TermStatus.INACTIVE),
        ]
        self.matcher.build(terms)

        text = "Python and Java"
        result = self.matcher.protect_text(text)

        assert len(result.matched_terms) == 1
        assert result.matched_terms[0].original_text == "Python"

    def test_rebuild_matcher(self):
        """Test rebuilding matcher with new terms."""
        terms1 = [create_test_term("Python")]
        self.matcher.build(terms1)

        result = self.matcher.protect_text("Python is great")
        assert len(result.matched_terms) == 1

        # Rebuild with different terms
        terms2 = [create_test_term("Java")]
        self.matcher.build(terms2)

        result = self.matcher.protect_text("Python is great")
        assert len(result.matched_terms) == 0

        result = self.matcher.protect_text("Java is great")
        assert len(result.matched_terms) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
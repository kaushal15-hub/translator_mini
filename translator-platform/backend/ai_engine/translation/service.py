"""
Translation Service

Main translation service integrating terminology protection, context handling, and model inference.
"""

import time
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from dataclasses import dataclass

from app.ai_engine.terminology.matcher import (
    TerminologyMatcher,
    get_terminology_matcher,
    ProtectionResult,
)
from app.ai_engine.context.manager import ConversationContextManager
from app.inference.scheduler import InferenceScheduler, get_inference_scheduler
from app.inference.model_loader import ModelLoader, get_model_loader
from app.models.glossary import GlossaryTerm
from app.schemas.ticket import TranslationRequest, TranslationResponse, LanguageCode, ConversationDomain

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Internal translation result."""

    translated_text: str
    protected_terms: Dict[str, str]
    translation_time_ms: float
    model_used: str
    glossary_applied: bool


class TranslationService:
    """
    Main translation service orchestrating the full translation pipeline.

    Pipeline:
    1. Load domain-specific glossary terms
    2. Build terminology matcher
    3. Protect terminology with placeholders
    4. Get conversation context
    5. Run translation inference
    6. Restore protected terms
    7. Validate restoration
    """

    def __init__(self):
        self._matcher: Optional[TerminologyMatcher] = None
        self._context_manager = ConversationContextManager()
        self._scheduler: Optional[InferenceScheduler] = None
        self._model_loader: Optional[ModelLoader] = None
        self._current_glossary_terms: List[GlossaryTerm] = []

    async def initialize(self) -> None:
        """Initialize translation service components."""
        self._scheduler = await get_inference_scheduler()
        self._model_loader = await get_model_loader()
        await self._model_loader.load_translation_models()
        logger.info("Translation service initialized")

    async def set_glossary_terms(self, terms: List[GlossaryTerm]) -> None:
        """
        Set glossary terms for terminology protection.

        Args:
            terms: List of active glossary terms
        """
        self._current_glossary_terms = terms
        self._matcher = get_terminology_matcher()
        self._matcher.build(terms)
        logger.info(f"Built terminology matcher with {len(terms)} terms")

    async def translate(self, request: TranslationRequest) -> TranslationResponse:
        """
        Translate text with terminology protection and context awareness.

        Args:
            request: Translation request

        Returns:
            Translation response
        """
        start_time = time.time()

        # Ensure matcher is built
        if not self._matcher or not self._current_glossary_terms:
            logger.warning("No glossary terms loaded, translating without terminology protection")
            return await self._translate_without_protection(request, start_time)

        # Step 1: Protect terminology
        protection_result = self._matcher.protect_text(request.text)

        # Step 2: Get conversation context
        context = await self._context_manager.get_context(
            room_id=request.context_messages,  # Using context_messages as room_id for now
            max_messages=4,
        )

        # Step 3: Prepare translation input
        translation_input = self._prepare_translation_input(
            protection_result.protected_text,
            request.source_language,
            request.target_language,
            request.domain,
            context,
        )

        # Step 4: Run inference
        inference_result = await self._run_inference(translation_input, request)

        # Step 5: Restore terminology
        restored_text = self._matcher.restore_text(
            inference_result, protection_result.placeholder_map
        )

        # Step 6: Validate restoration
        is_valid, errors = self._matcher.validate_restoration(
            request.text, restored_text, protection_result.matched_terms
        )

        if not is_valid:
            logger.warning(f"Terminology restoration validation failed: {errors}")
            # Fallback: try to restore anyway
            pass

        translation_time = (time.time() - start_time) * 1000

        return TranslationResponse(
            original_text=request.text,
            translated_text=restored_text,
            source_language=request.source_language,
            target_language=request.target_language,
            domain=request.domain,
            protected_terms=protection_result.placeholder_map,
            translation_time_ms=translation_time,
            model_used="indictrans2-distilled",
            glossary_applied=len(protection_result.matched_terms) > 0,
        )

    async def _translate_without_protection(
        self, request: TranslationRequest, start_time: float
    ) -> TranslationResponse:
        """Translate without terminology protection (fallback)."""
        # Get context
        context = await self._context_manager.get_context(
            room_id=request.context_messages,
            max_messages=4,
        )

        translation_input = self._prepare_translation_input(
            request.text,
            request.source_language,
            request.target_language,
            request.domain,
            context,
        )

        inference_result = await self._run_inference(translation_input, request)

        translation_time = (time.time() - start_time) * 1000

        return TranslationResponse(
            original_text=request.text,
            translated_text=inference_result,
            source_language=request.source_language,
            target_language=request.target_language,
            domain=request.domain,
            protected_terms={},
            translation_time_ms=translation_time,
            model_used="indictrans2-distilled",
            glossary_applied=False,
        )

    def _prepare_translation_input(
        self,
        text: str,
        source_lang: LanguageCode,
        target_lang: LanguageCode,
        domain: ConversationDomain,
        context: List[str],
    ) -> str:
        """
        Prepare input for translation model with context.

        Args:
            text: Text to translate (with placeholders)
            source_lang: Source language
            target_lang: Target language
            domain: Conversation domain
            context: Previous messages for context

        Returns:
            Formatted input for model
        """
        # Build context prefix
        context_str = ""
        if context:
            context_str = " [CONTEXT] " + " | ".join(context[-3:])  # Last 3 messages

        # Domain tag for model
        domain_tags = {
            ConversationDomain.TECHNOLOGY: "[TECH]",
            ConversationDomain.MEDICAL: "[MEDICAL]",
            ConversationDomain.GENERAL: "[GENERAL]",
        }
        domain_tag = domain_tags.get(domain, "[GENERAL]")

        # Language tags for IndicTrans2
        lang_tags = {
            LanguageCode.ENGLISH: "eng_Latn",
            LanguageCode.KANNADA: "kan_Knda",
            LanguageCode.HINDI: "hin_Deva",
            LanguageCode.MALAYALAM: "mal_Mlym",
            LanguageCode.TAMIL: "tam_Taml",
        }
        src_tag = lang_tags.get(source_lang, "eng_Latn")
        tgt_tag = lang_tags.get(target_lang, "kan_Knda")

        # Format: [SRC_LANG] [TGT_LANG] [DOMAIN] [CONTEXT] TEXT
        return f"{src_tag} {tgt_tag} {domain_tag}{context_str} {text}"

    async def _run_inference(self, input_text: str, request: TranslationRequest) -> str:
        """
        Run translation inference.

        Args:
            input_text: Prepared input text
            request: Translation request

        Returns:
            Translated text
        """
        if not self._scheduler or not self._model_loader:
            # Fallback for testing without models
            return self._fallback_translate(input_text, request.source_language, request.target_language)

        # Submit to inference queue
        result = await self._scheduler.submit(
            model_name="indictrans2",
            input_data={
                "text": input_text,
                "source_lang": request.source_language.value,
                "target_lang": request.target_language.value,
            },
            timeout=30,
        )

        return result.get("translation", input_text)

    def _fallback_translate(self, text: str, source_lang: LanguageCode, target_lang: LanguageCode) -> str:
        """
        Fallback translation for testing without models.

        Args:
            text: Input text
            source_lang: Source language
            target_lang: Target language

        Returns:
            Mock translated text
        """
        # This is a clear fallback - NOT real translation
        lang_names = {
            LanguageCode.ENGLISH: "English",
            LanguageCode.KANNADA: "Kannada",
            LanguageCode.HINDI: "Hindi",
            LanguageCode.MALAYALAM: "Malayalam",
            LanguageCode.TAMIL: "Tamil",
        }

        src_name = lang_names.get(source_lang, source_lang.value)
        tgt_name = lang_names.get(target_lang, target_lang.value)

        return f"[FALLBACK {src_name}→{tgt_name}] {text}"


# Global service instance
_translation_service: Optional[TranslationService] = None


async def get_translation_service() -> TranslationService:
    """Get or create global translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
        await _translation_service.initialize()
    return _translation_service
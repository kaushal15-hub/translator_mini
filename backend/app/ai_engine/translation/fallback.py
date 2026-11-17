from .base import TranslationAdapter
class DevelopmentFallback(TranslationAdapter):
    async def translate(self, text, source, target, domain, context):
        # Deliberately does not pretend to translate: use only for wiring and UI development.
        return text

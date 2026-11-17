from abc import ABC, abstractmethod
class TranslationAdapter(ABC):
    @abstractmethod
    async def translate(self, text: str, source: str, target: str, domain: str, context: list[dict]) -> str: ...

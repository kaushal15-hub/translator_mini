"""
Conversation Context Manager

Manages bounded conversation context for translation.
"""

import logging
from typing import List, Dict, Optional
from uuid import UUID
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Single context entry."""

    message_id: str
    text: str
    source_language: str
    target_language: str
    domain: str
    timestamp: datetime
    sender_id: str


class ConversationContextManager:
    """
    Manages conversation context for translation.

    Features:
    - Bounded context window (last N messages)
    - Per-room context isolation
    - Automatic cleanup of old contexts
    - Language-aware context filtering
    """

    def __init__(self, max_context_size: int = 4, max_context_age_hours: int = 24):
        self.max_context_size = max_context_size
        self.max_context_age = timedelta(hours=max_context_age_hours)
        self._contexts: Dict[str, deque] = {}  # room_id -> deque of ContextEntry
        self._last_access: Dict[str, datetime] = {}

    def _get_room_key(self, room_id: str) -> str:
        """Get context key for room."""
        return f"room:{room_id}"

    def add_message(
        self,
        room_id: str,
        message_id: str,
        text: str,
        source_language: str,
        target_language: str,
        domain: str,
        sender_id: str,
    ) -> None:
        """
        Add a message to conversation context.

        Args:
            room_id: Room identifier
            message_id: Unique message ID
            text: Message text (original)
            source_language: Source language code
            target_language: Target language code
            domain: Conversation domain
            sender_id: Sender user ID
        """
        key = self._get_room_key(room_id)

        if key not in self._contexts:
            self._contexts[key] = deque(maxlen=self.max_context_size)

        entry = ContextEntry(
            message_id=message_id,
            text=text,
            source_language=source_language,
            target_language=target_language,
            domain=domain,
            timestamp=datetime.utcnow(),
            sender_id=sender_id,
        )

        self._contexts[key].append(entry)
        self._last_access[key] = datetime.utcnow()

    def get_context(
        self,
        room_id: str,
        max_messages: Optional[int] = None,
        target_language: Optional[str] = None,
    ) -> List[str]:
        """
        Get conversation context for translation.

        Args:
            room_id: Room identifier
            max_messages: Maximum messages to return (default: max_context_size)
            target_language: Filter by target language (optional)

        Returns:
            List of context messages (most recent first)
        """
        key = self._get_room_key(room_id)

        if key not in self._contexts:
            return []

        self._last_access[key] = datetime.utcnow()

        messages = list(self._contexts[key])

        # Filter by target language if specified
        if target_language:
            messages = [m for m in messages if m.target_language == target_language]

        # Limit messages
        limit = max_messages or self.max_context_size
        messages = messages[-limit:]

        # Return text only, most recent first
        return [m.text for m in reversed(messages)]

    def get_context_with_metadata(
        self,
        room_id: str,
        max_messages: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get conversation context with full metadata.

        Args:
            room_id: Room identifier
            max_messages: Maximum messages to return

        Returns:
            List of context entries with metadata
        """
        key = self._get_room_key(room_id)

        if key not in self._contexts:
            return []

        self._last_access[key] = datetime.utcnow()

        messages = list(self._contexts[key])
        limit = max_messages or self.max_context_size
        messages = messages[-limit:]

        return [
            {
                "message_id": m.message_id,
                "text": m.text,
                "source_language": m.source_language,
                "target_language": m.target_language,
                "domain": m.domain,
                "timestamp": m.timestamp.isoformat(),
                "sender_id": m.sender_id,
            }
            for m in reversed(messages)
        ]

    def clear_context(self, room_id: str) -> bool:
        """
        Clear context for a room.

        Args:
            room_id: Room identifier

        Returns:
            True if context was cleared
        """
        key = self._get_room_key(room_id)
        if key in self._contexts:
            del self._contexts[key]
            if key in self._last_access:
                del self._last_access[key]
            return True
        return False

    def get_context_size(self, room_id: str) -> int:
        """Get current context size for a room."""
        key = self._get_room_key(room_id)
        return len(self._contexts.get(key, []))

    def cleanup_old_contexts(self) -> int:
        """
        Clean up contexts older than max_context_age.

        Returns:
            Number of contexts cleaned up
        """
        now = datetime.utcnow()
        keys_to_delete = []

        for key, last_access in self._last_access.items():
            if now - last_access > self.max_context_age:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            if key in self._contexts:
                del self._contexts[key]
            del self._last_access[key]

        return len(keys_to_delete)

    def get_stats(self) -> Dict:
        """Get context manager statistics."""
        return {
            "active_rooms": len(self._contexts),
            "total_messages": sum(len(ctx) for ctx in self._contexts.values()),
            "max_context_size": self.max_context_size,
            "max_context_age_hours": self.max_context_age.total_seconds() / 3600,
        }


# Global context manager instance
_context_manager: Optional[ConversationContextManager] = None


def get_context_manager() -> ConversationContextManager:
    """Get or create global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ConversationContextManager()
    return _context_manager
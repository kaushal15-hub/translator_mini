"""
WebSocket Connection Manager

Manages WebSocket connections, rooms, and message broadcasting.
"""

import json
import logging
from typing import Dict, List, Optional, Set
from uuid import UUID
from dataclasses import dataclass, field
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.models.user import User
from app.models.ticket import Message, LanguageCode, ConversationDomain
from app.ai_engine.translation.service import get_translation_service
from app.ai_engine.terminology.matcher import get_terminology_matcher
from app.ai_engine.context.manager import get_context_manager
from app.glossary.service import GlossaryService
from app.core.database import get_db_context
from app.tickets.service import TicketService

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """WebSocket connection info."""

    websocket: WebSocket
    user_id: UUID
    user: User
    room_id: Optional[UUID] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)


class ConnectionManager:
    """
    Manages WebSocket connections and room messaging.

    Features:
    - Connection authentication
    - Room-based message routing
    - Translation integration
    - Connection lifecycle management
    - Ping/pong keepalive
    """

    def __init__(self):
        self._connections: Dict[UUID, Connection] = {}  # connection_id -> Connection
        self._user_connections: Dict[UUID, Set[UUID]] = {}  # user_id -> set of connection_ids
        self._room_connections: Dict[UUID, Set[UUID]] = {}  # room_id -> set of connection_ids
        self._translation_service = None
        self._terminology_matcher = None
        self._context_manager = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize WebSocket manager with AI services."""
        if self._initialized:
            return

        self._translation_service = await get_translation_service()
        self._terminology_matcher = get_terminology_matcher()
        self._context_manager = get_context_manager()
        self._initialized = True
        logger.info("WebSocket manager initialized")

    async def connect(
        self, websocket: WebSocket, token: str
    ) -> Optional[Connection]:
        """
        Authenticate and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            token: JWT access token

        Returns:
            Connection object if authenticated, None otherwise
        """
        # Verify token
        payload = decode_access_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Invalid token")
            return None

        user_id = UUID(payload.get("sub", ""))
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token payload")
            return None

        # Get user from database
        async with get_db_context() as db:
            from sqlalchemy import select
            from app.models.user import User
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

        if not user or user.status.value != "active":
            await websocket.close(code=4002, reason="User not found or inactive")
            return None

        # Accept connection
        await websocket.accept()

        # Create connection
        connection_id = UUID(int=hash((user_id, datetime.utcnow().timestamp())) % (2**128))
        connection = Connection(
            websocket=websocket,
            user_id=user_id,
            user=user,
        )

        # Register connection
        self._connections[connection_id] = connection
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection_id)

        logger.info(f"User {user.email} connected (connection: {connection_id})")
        return connection

    def disconnect(self, connection_id: UUID) -> None:
        """
        Disconnect and clean up a connection.

        Args:
            connection_id: Connection to disconnect
        """
        connection = self._connections.pop(connection_id, None)
        if not connection:
            return

        # Remove from user connections
        user_conns = self._user_connections.get(connection.user_id, set())
        user_conns.discard(connection_id)
        if not user_conns:
            self._user_connections.pop(connection.user_id, None)

        # Remove from room connections
        if connection.room_id:
            room_conns = self._room_connections.get(connection.room_id, set())
            room_conns.discard(connection_id)
            if not room_conns:
                self._room_connections.pop(connection.room_id, None)

        logger.info(f"User {connection.user.email} disconnected (connection: {connection_id})")

    async def join_room(self, connection_id: UUID, room_id: UUID) -> bool:
        """
        Add connection to a room.

        Args:
            connection_id: Connection ID
            room_id: Room ID

        Returns:
            True if joined successfully
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False

        # Verify user is member of room
        async with get_db_context() as db:
            ticket_service = TicketService(db)
            is_member = await ticket_service.is_user_in_room(room_id, connection.user_id)

        if not is_member:
            return False

        # Leave current room if any
        if connection.room_id:
            await self.leave_room(connection_id)

        # Join new room
        connection.room_id = room_id
        if room_id not in self._room_connections:
            self._room_connections[room_id] = set()
        self._room_connections[room_id].add(connection_id)

        # Notify room of new member
        await self._broadcast_to_room(
            room_id,
            {
                "type": "user_joined",
                "user_id": str(connection.user_id),
                "user_name": connection.user.full_name,
                "timestamp": datetime.utcnow().isoformat(),
            },
            exclude_connection=connection_id,
        )

        logger.info(f"User {connection.user.email} joined room {room_id}")
        return True

    async def leave_room(self, connection_id: UUID) -> bool:
        """
        Remove connection from current room.

        Args:
            connection_id: Connection ID

        Returns:
            True if left room
        """
        connection = self._connections.get(connection_id)
        if not connection or not connection.room_id:
            return False

        room_id = connection.room_id
        connection.room_id = None

        room_conns = self._room_connections.get(room_id, set())
        room_conns.discard(connection_id)
        if not room_conns:
            self._room_connections.pop(room_id, None)

        # Notify room of member leaving
        await self._broadcast_to_room(
            room_id,
            {
                "type": "user_left",
                "user_id": str(connection.user_id),
                "user_name": connection.user.full_name,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"User {connection.user.email} left room {room_id}")
        return True

    async def send_message(
        self, connection_id: UUID, room_id: UUID, text: str
    ) -> Optional[Message]:
        """
        Send a message to a room with translation.

        Args:
            connection_id: Sender connection ID
            room_id: Room ID
            text: Message text

        Returns:
            Created message with translations
        """
        connection = self._connections.get(connection_id)
        if not connection or connection.room_id != room_id:
            return None

        # Get room info for language settings
        async with get_db_context() as db:
            ticket_service = TicketService(db)
            room = await ticket_service.get_room_by_id(room_id)
            if not room:
                return None

            # Get glossary terms for domain
            glossary_service = GlossaryService(db)
            terms = await glossary_service.get_active_terms_for_domain(
                room.domain, room.source_language.value, room.target_language.value
            )

        # Set glossary terms for translation
        if terms:
            await self._translation_service.set_glossary_terms(terms)
            self._terminology_matcher.build(terms)

        # Translate message
        from app.schemas.ticket import TranslationRequest, LanguageCode, ConversationDomain

        # Get context
        context = self._context_manager.get_context(str(room_id), max_messages=4)

        translation_request = TranslationRequest(
            text=text,
            source_language=LanguageCode(room.source_language),
            target_language=LanguageCode(room.target_language),
            domain=ConversationDomain(room.domain),
            context_messages=context,
        )

        translation_response = await self._translation_service.translate(translation_request)

        # Create message record
        async with get_db_context() as db:
            message = Message(
                room_id=room_id,
                sender_id=connection.user_id,
                original_text=text,
                original_language=LanguageCode(room.source_language),
                translated_text=translation_response.translated_text,
                translated_language=LanguageCode(room.target_language),
                domain=ConversationDomain(room.domain),
                glossary_applied=translation_response.glossary_applied,
                protected_terms=translation_response.protected_terms,
                translation_metadata={
                    "translation_time_ms": translation_response.translation_time_ms,
                    "model_used": translation_response.model_used,
                },
            )
            db.add(message)
            await db.flush()
            await db.refresh(message)

            # Add to context
            self._context_manager.add_message(
                room_id=str(room_id),
                message_id=str(message.id),
                text=text,
                source_language=room.source_language.value,
                target_language=room.target_language.value,
                domain=room.domain.value,
                sender_id=str(connection.user_id),
            )

        # Broadcast to room
        await self._broadcast_to_room(
            room_id,
            {
                "type": "message",
                "message": {
                    "id": str(message.id),
                    "sender_id": str(connection.user_id),
                    "sender_name": connection.user.full_name,
                    "original_text": text,
                    "original_language": room.source_language.value,
                    "translated_text": translation_response.translated_text,
                    "translated_language": room.target_language.value,
                    "domain": room.domain.value,
                    "glossary_applied": translation_response.glossary_applied,
                    "protected_terms": translation_response.protected_terms,
                    "timestamp": message.created_at.isoformat(),
                },
            },
        )

        return message

    async def send_typing_indicator(self, connection_id: UUID, room_id: UUID, is_typing: bool) -> None:
        """Send typing indicator to room."""
        connection = self._connections.get(connection_id)
        if not connection or connection.room_id != room_id:
            return

        await self._broadcast_to_room(
            room_id,
            {
                "type": "typing",
                "user_id": str(connection.user_id),
                "user_name": connection.user.full_name,
                "is_typing": is_typing,
            },
            exclude_connection=connection_id,
        )

    async def _broadcast_to_room(
        self,
        room_id: UUID,
        message: dict,
        exclude_connection: Optional[UUID] = None,
    ) -> None:
        """Broadcast message to all connections in a room."""
        connection_ids = self._room_connections.get(room_id, set())

        for conn_id in connection_ids:
            if conn_id == exclude_connection:
                continue

            connection = self._connections.get(conn_id)
            if not connection:
                continue

            try:
                await connection.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send to connection {conn_id}: {e}")
                # Connection will be cleaned up on next ping

    def get_room_connections(self, room_id: UUID) -> List[Connection]:
        """Get all connections in a room."""
        connection_ids = self._room_connections.get(room_id, set())
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]

    def get_user_connections(self, user_id: UUID) -> List[Connection]:
        """Get all connections for a user."""
        connection_ids = self._user_connections.get(user_id, set())
        return [self._connections[cid] for cid in connection_ids if cid in self._connections]

    def get_connection_count(self) -> int:
        """Get total connection count."""
        return len(self._connections)

    def get_room_connection_count(self, room_id: UUID) -> int:
        """Get connection count for a room."""
        return len(self._room_connections.get(room_id, set()))


# Global connection manager
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create global connection manager."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
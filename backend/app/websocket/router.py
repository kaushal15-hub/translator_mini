"""
WebSocket Router

API endpoints for real-time communication.
"""

import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.websocket.manager import ConnectionManager, get_connection_manager
from app.tickets.service import TicketService
from app.schemas.user import UserResponse
from app.models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)


async def get_current_user_ws(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current user from WebSocket token.

    Args:
        token: JWT access token from query parameter
        db: Database session

    Returns:
        Authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    stmt = select(User).where(User.id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.status.value != "active":
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    WebSocket endpoint for real-time communication.

    Query Parameters:
        token: JWT access token

    Message Types (Client -> Server):
        - join_room: Join a communication room
        - leave_room: Leave current room
        - send_message: Send a message to current room
        - typing: Send typing indicator
        - ping: Keepalive ping

    Message Types (Server -> Client):
        - connected: Connection established
        - user_joined: User joined room
        - user_left: User left room
        - message: New message received
        - typing: Typing indicator
        - pong: Keepalive pong
        - error: Error message
    """
    manager = get_connection_manager()

    # Authenticate user
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    # Get user from database
    stmt = select(User).where(User.id == UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or user.status.value != "active":
        await websocket.close(code=4002, reason="User not found or inactive")
        return

    # Initialize manager if needed
    await manager.initialize()

    # Connect
    connection = await manager.connect(websocket, token)
    if not connection:
        return

    connection_id = list(manager._connections.keys())[
        list(manager._connections.values()).index(connection)
    ]

    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "user_id": str(user.id),
            "user_name": user.full_name,
            "connection_id": str(connection_id),
            "timestamp": connection.connected_at.isoformat(),
        }))

        # Message handling loop
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_message(manager, connection_id, message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.email}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.email}: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e),
            }))
        except Exception:
            pass
    finally:
        manager.disconnect(connection_id)


async def handle_message(
    manager: ConnectionManager,
    connection_id: UUID,
    message: dict,
) -> None:
    """
    Handle incoming WebSocket message.

    Args:
        manager: Connection manager
        connection_id: Sender connection ID
        message: Parsed message dict
    """
    msg_type = message.get("type")

    if msg_type == "join_room":
        await handle_join_room(manager, connection_id, message)

    elif msg_type == "leave_room":
        await handle_leave_room(manager, connection_id)

    elif msg_type == "send_message":
        await handle_send_message(manager, connection_id, message)

    elif msg_type == "typing":
        await handle_typing(manager, connection_id, message)

    elif msg_type == "ping":
        await handle_ping(manager, connection_id)

    else:
        connection = manager._connections.get(connection_id)
        if connection:
            await connection.websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Unknown message type: {msg_type}",
            }))


async def handle_join_room(
    manager: ConnectionManager,
    connection_id: UUID,
    message: dict,
) -> None:
    """Handle join room request."""
    room_id_str = message.get("room_id")
    if not room_id_str:
        await send_error(manager, connection_id, "room_id required")
        return

    try:
        room_id = UUID(room_id_str)
    except ValueError:
        await send_error(manager, connection_id, "Invalid room_id")
        return

    success = await manager.join_room(connection_id, room_id)

    connection = manager._connections.get(connection_id)
    if connection:
        await connection.websocket.send_text(json.dumps({
            "type": "join_room_response",
            "room_id": room_id_str,
            "success": success,
        }))


async def handle_leave_room(
    manager: ConnectionManager,
    connection_id: UUID,
) -> None:
    """Handle leave room request."""
    await manager.leave_room(connection_id)

    connection = manager._connections.get(connection_id)
    if connection:
        await connection.websocket.send_text(json.dumps({
            "type": "leave_room_response",
            "success": True,
        }))


async def handle_send_message(
    manager: ConnectionManager,
    connection_id: UUID,
    message: dict,
) -> None:
    """Handle send message request."""
    room_id_str = message.get("room_id")
    text = message.get("text")

    if not room_id_str or not text:
        await send_error(manager, connection_id, "room_id and text required")
        return

    try:
        room_id = UUID(room_id_str)
    except ValueError:
        await send_error(manager, connection_id, "Invalid room_id")
        return

    # Send message (includes translation)
    msg = await manager.send_message(connection_id, room_id, text)

    if not msg:
        await send_error(manager, connection_id, "Failed to send message")


async def handle_typing(
    manager: ConnectionManager,
    connection_id: UUID,
    message: dict,
) -> None:
    """Handle typing indicator."""
    room_id_str = message.get("room_id")
    is_typing = message.get("is_typing", False)

    if not room_id_str:
        return

    try:
        room_id = UUID(room_id_str)
    except ValueError:
        return

    await manager.send_typing_indicator(connection_id, room_id, is_typing)


async def handle_ping(
    manager: ConnectionManager,
    connection_id: UUID,
) -> None:
    """Handle ping (keepalive)."""
    connection = manager._connections.get(connection_id)
    if connection:
        connection.last_ping = connection.last_ping  # Update timestamp
        await connection.websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": connection.last_ping.isoformat(),
        }))


async def send_error(
    manager: ConnectionManager,
    connection_id: UUID,
    message: str,
) -> None:
    """Send error message to connection."""
    connection = manager._connections.get(connection_id)
    if connection:
        await connection.websocket.send_text(json.dumps({
            "type": "error",
            "message": message,
        }))
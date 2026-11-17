"""
Ticket Router

API endpoints for ticket and room management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.authentication.router import (
    get_current_active_user,
    get_current_admin,
    get_current_room_agent,
)
from app.tickets.service import TicketService
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketAdminUpdate,
    TicketResponse,
    TicketDetailResponse,
    TicketListResponse,
    RoomCreate,
    RoomUpdate,
    RoomResponse,
    RoomDetailResponse,
    RoomListResponse,
    RoomMemberCreate,
    RoomMemberUpdate,
    RoomMemberResponse,
    TicketStatus,
)
from app.schemas.user import UserResponse

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def get_ticket_service(db: AsyncSession = Depends(get_db)) -> TicketService:
    """Get ticket service instance."""
    return TicketService(db)


# ============================================
# User Ticket Endpoints
# ============================================


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED, summary="Create a new ticket")
async def create_ticket(
    ticket_data: TicketCreate,
    current_user: UserResponse = Depends(get_current_active_user),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Create a new communication ticket.

    Args:
        ticket_data: Ticket creation data
        current_user: Current authenticated user
        ticket_service: Ticket service

    Returns:
        Created ticket
    """
    ticket = await ticket_service.create_ticket(UUID(current_user.id), ticket_data)
    return TicketResponse.model_validate(ticket)


@router.get("", response_model=TicketListResponse, summary="List user's tickets")
async def list_my_tickets(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TicketStatus] = None,
    current_user: UserResponse = Depends(get_current_active_user),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketListResponse:
    """
    List current user's tickets (created or assigned).

    Args:
        page: Page number
        size: Page size
        status_filter: Optional status filter
        current_user: Current authenticated user
        ticket_service: Ticket service

    Returns:
        Paginated ticket list
    """
    tickets, total = await ticket_service.list_user_tickets(
        UUID(current_user.id), page, size, status_filter
    )
    return TicketListResponse(
        tickets=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{ticket_id}", response_model=TicketDetailResponse, summary="Get ticket details")
async def get_ticket(
    ticket_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketDetailResponse:
    """
    Get ticket details.

    Args:
        ticket_id: Ticket ID
        current_user: Current authenticated user
        ticket_service: Ticket service

    Returns:
        Ticket details
    """
    ticket = await ticket_service.get_ticket_detail(ticket_id)

    # Check access: creator, assignee, or admin
    user_id = UUID(current_user.id)
    is_admin = current_user.is_superuser or "admin" in [r.name for r in current_user.roles]

    if not is_admin and ticket.created_by_id != user_id and ticket.assigned_to_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied to this ticket")

    # Build detailed response
    response = TicketDetailResponse.model_validate(ticket)
    if ticket.creator:
        response.creator_name = ticket.creator.full_name
        response.creator_email = ticket.creator.email
    if ticket.assignee:
        response.assignee_name = ticket.assignee.full_name
        response.assignee_email = ticket.assignee.email
    if ticket.room:
        response.room_name = ticket.room.name

    return response


@router.put("/{ticket_id}", response_model=TicketResponse, summary="Update ticket")
async def update_ticket(
    ticket_id: UUID,
    ticket_data: TicketUpdate,
    current_user: UserResponse = Depends(get_current_active_user),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Update a ticket (only by creator, only if pending).

    Args:
        ticket_id: Ticket ID
        ticket_data: Update data
        current_user: Current authenticated user
        ticket_service: Ticket service

    Returns:
        Updated ticket
    """
    ticket = await ticket_service.update_ticket(
        ticket_id, UUID(current_user.id), ticket_data
    )
    return TicketResponse.model_validate(ticket)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Cancel ticket")
async def cancel_ticket(
    ticket_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> None:
    """
    Cancel a ticket (only by creator, only if pending or rejected).

    Args:
        ticket_id: Ticket ID
        current_user: Current authenticated user
        ticket_service: Ticket service
    """
    await ticket_service.delete_ticket(ticket_id, UUID(current_user.id))


# ============================================
# Admin Ticket Endpoints
# ============================================


@router.get("/admin/all", response_model=TicketListResponse, summary="List all tickets (admin)")
async def list_all_tickets(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TicketStatus] = None,
    domain_filter: Optional[str] = None,
    assignee_filter: Optional[UUID] = None,
    current_user: UserResponse = Depends(get_current_admin),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketListResponse:
    """
    List all tickets (admin only).

    Args:
        page: Page number
        size: Page size
        status_filter: Optional status filter
        domain_filter: Optional domain filter
        assignee_filter: Optional assignee filter
        current_user: Current admin user
        ticket_service: Ticket service

    Returns:
        Paginated ticket list
    """
    tickets, total = await ticket_service.list_all_tickets(
        page, size, status_filter, domain_filter, assignee_filter
    )
    return TicketListResponse(
        tickets=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.post("/{ticket_id}/approve", response_model=TicketResponse, summary="Approve ticket (admin)")
async def approve_ticket(
    ticket_id: UUID,
    current_user: UserResponse = Depends(get_current_admin),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Approve a pending ticket (admin only).

    Args:
        ticket_id: Ticket ID
        current_user: Current admin user
        ticket_service: Ticket service

    Returns:
        Approved ticket
    """
    ticket = await ticket_service.approve_ticket(ticket_id, UUID(current_user.id))
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/reject", response_model=TicketResponse, summary="Reject ticket (admin)")
async def reject_ticket(
    ticket_id: UUID,
    reason: str,
    current_user: UserResponse = Depends(get_current_admin),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Reject a pending ticket (admin only).

    Args:
        ticket_id: Ticket ID
        reason: Rejection reason
        current_user: Current admin user
        ticket_service: Ticket service

    Returns:
        Rejected ticket
    """
    ticket = await ticket_service.reject_ticket(ticket_id, UUID(current_user.id), reason)
    return TicketResponse.model_validate(ticket)


@router.post("/{ticket_id}/assign", response_model=TicketResponse, summary="Assign ticket to room agent (admin)")
async def assign_ticket(
    ticket_id: UUID,
    assignee_id: UUID,
    current_user: UserResponse = Depends(get_current_admin),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Assign ticket to a room agent (admin only).

    Args:
        ticket_id: Ticket ID
        assignee_id: Room agent user ID
        current_user: Current admin user
        ticket_service: Ticket service

    Returns:
        Assigned ticket
    """
    ticket = await ticket_service.assign_ticket(ticket_id, assignee_id, UUID(current_user.id))
    return TicketResponse.model_validate(ticket)


@router.put("/{ticket_id}/admin", response_model=TicketResponse, summary="Update ticket (admin)")
async def update_ticket_admin(
    ticket_id: UUID,
    ticket_data: TicketAdminUpdate,
    current_user: UserResponse = Depends(get_current_admin),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> TicketResponse:
    """
    Update ticket as admin (admin only).

    Args:
        ticket_id: Ticket ID
        ticket_data: Admin update data
        current_user: Current admin user
        ticket_service: Ticket service

    Returns:
        Updated ticket
    """
    ticket = await ticket_service.update_ticket_admin(ticket_id, ticket_data)
    return TicketResponse.model_validate(ticket)


# ============================================
# Room Endpoints
# ============================================


@router.post("/{ticket_id}/room", response_model=RoomResponse, status_code=status.HTTP_201_CREATED, summary="Create room for ticket")
async def create_room_for_ticket(
    ticket_id: UUID,
    room_data: RoomCreate,
    current_user: UserResponse = Depends(get_current_room_agent),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> RoomResponse:
    """
    Create a communication room for a ticket (room agent or admin).

    Args:
        ticket_id: Ticket ID
        room_data: Room creation data
        current_user: Current room agent or admin
        ticket_service: Ticket service

    Returns:
        Created room
    """
    room = await ticket_service.create_room(UUID(current_user.id), room_data)
    # Link ticket to room
    await ticket_service.link_ticket_to_room(ticket_id, room.id)
    return RoomResponse.model_validate(room)


@router.get("/rooms/my", response_model=RoomListResponse, summary="List user's rooms")
async def list_my_rooms(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_active_user),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> RoomListResponse:
    """
    List rooms the current user is a member of.

    Args:
        page: Page number
        size: Page size
        current_user: Current authenticated user
        ticket_service: Ticket service

    Returns:
        Paginated room list
    """
    rooms, total = await ticket_service.list_user_rooms(UUID(current_user.id), page, size)
    return RoomListResponse(
        rooms=[RoomResponse.model_validate(r) for r in rooms],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/rooms/{room_id}", response_model=RoomDetailResponse, summary="Get room details")
async def get_room(
    room_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> RoomDetailResponse:
    """
    Get room details (only if user is member).

    Args:
        room_id: Room ID
        current_user: Current authenticated user
        ticket_service: Ticket service

    Returns:
        Room details with members
    """
    # Check membership
    is_member = await ticket_service.is_user_in_room(room_id, UUID(current_user.id))
    is_admin = current_user.is_superuser or "admin" in [r.name for r in current_user.roles]

    if not is_member and not is_admin:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    room = await ticket_service.get_room_detail(room_id)

    # Build detailed response
    response = RoomDetailResponse.model_validate(room)
    if room.creator:
        response.creator_name = room.creator.full_name
    response.member_count = len([m for m in room.members if m.is_active])
    response.members = [
        RoomMemberResponse.model_validate(m) for m in room.members if m.is_active
    ]

    return response


@router.put("/rooms/{room_id}", response_model=RoomResponse, summary="Update room")
async def update_room(
    room_id: UUID,
    room_data: RoomUpdate,
    current_user: UserResponse = Depends(get_current_room_agent),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> RoomResponse:
    """
    Update a room (room agent or admin).

    Args:
        room_id: Room ID
        room_data: Update data
        current_user: Current room agent or admin
        ticket_service: Ticket service

    Returns:
        Updated room
    """
    room = await ticket_service.update_room(room_id, room_data)
    return RoomResponse.model_validate(room)


# ============================================
# Room Member Endpoints
# ============================================


@router.post("/rooms/{room_id}/members", response_model=RoomMemberResponse, status_code=status.HTTP_201_CREATED, summary="Add member to room")
async def add_room_member(
    room_id: UUID,
    member_data: RoomMemberCreate,
    current_user: UserResponse = Depends(get_current_room_agent),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> RoomMemberResponse:
    """
    Add a member to a room (room agent or admin).

    Args:
        room_id: Room ID
        member_data: Member data
        current_user: Current room agent or admin
        ticket_service: Ticket service

    Returns:
        Created room member
    """
    member = await ticket_service.add_room_member(
        room_id, member_data.user_id, member_data.role
    )
    return RoomMemberResponse.model_validate(member)


@router.delete("/rooms/{room_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove member from room")
async def remove_room_member(
    room_id: UUID,
    user_id: UUID,
    current_user: UserResponse = Depends(get_current_room_agent),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> None:
    """
    Remove a member from a room (room agent or admin).

    Args:
        room_id: Room ID
        user_id: User ID to remove
        current_user: Current room agent or admin
        ticket_service: Ticket service
    """
    await ticket_service.remove_room_member(room_id, user_id)


@router.get("/rooms/{room_id}/members", response_model=list[RoomMemberResponse], summary="List room members")
async def list_room_members(
    room_id: UUID,
    current_user: UserResponse = Depends(get_current_active_user),
    ticket_service: TicketService = Depends(get_ticket_service),
) -> list[RoomMemberResponse]:
    """
    List members of a room (only if user is member).

    Args:
        room_id: Room ID
        current_user: Current authenticated user
        ticket_service: Ticket service

    Returns:
        List of room members
    """
    is_member = await ticket_service.is_user_in_room(room_id, UUID(current_user.id))
    is_admin = current_user.is_superuser or "admin" in [r.name for r in current_user.roles]

    if not is_member and not is_admin:
        raise HTTPException(status_code=403, detail="Not a member of this room")

    members = await ticket_service.get_room_members(room_id)
    return [RoomMemberResponse.model_validate(m) for m in members]
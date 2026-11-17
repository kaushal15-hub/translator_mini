"""
Ticket Service

Business logic for ticket management workflow.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    TicketNotFoundException,
    TicketStatusException,
    TicketAlreadyAssignedException,
    RoomNotFoundException,
    UserNotFoundException,
)
from app.models.ticket import Ticket, Room, RoomMember, TicketStatus, TicketPriority
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketUpdate, TicketAdminUpdate, RoomCreate, RoomUpdate


class TicketService:
    """Ticket management service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================
    # Ticket CRUD Operations
    # ============================================

    async def create_ticket(self, user_id: UUID, ticket_data: TicketCreate) -> Ticket:
        """
        Create a new communication ticket.

        Args:
            user_id: ID of user creating the ticket
            ticket_data: Ticket creation data

        Returns:
            Created ticket
        """
        ticket = Ticket(
            **ticket_data.model_dump(),
            created_by_id=user_id,
            status=TicketStatus.PENDING,
        )
        self.db.add(ticket)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def get_ticket_by_id(self, ticket_id: UUID) -> Optional[Ticket]:
        """Get ticket by ID with relationships loaded."""
        stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.creator),
                selectinload(Ticket.assignee),
                selectinload(Ticket.room),
            )
            .where(Ticket.id == ticket_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_ticket_detail(self, ticket_id: UUID) -> Ticket:
        """Get ticket by ID or raise exception."""
        ticket = await self.get_ticket_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundException()
        return ticket

    async def update_ticket(
        self, ticket_id: UUID, user_id: UUID, ticket_data: TicketUpdate
    ) -> Ticket:
        """
        Update ticket (only by creator, only if pending).

        Args:
            ticket_id: Ticket ID
            user_id: ID of user updating
            ticket_data: Update data

        Returns:
            Updated ticket
        """
        ticket = await self.get_ticket_detail(ticket_id)

        if ticket.created_by_id != user_id:
            raise TicketStatusException("Only the ticket creator can update it")

        if ticket.status != TicketStatus.PENDING:
            raise TicketStatusException("Can only update pending tickets")

        update_data = ticket_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ticket, field, value)

        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def delete_ticket(self, ticket_id: UUID, user_id: UUID) -> bool:
        """
        Delete/cancel ticket (only by creator, only if pending).

        Args:
            ticket_id: Ticket ID
            user_id: ID of user deleting

        Returns:
            True if deleted
        """
        ticket = await self.get_ticket_detail(ticket_id)

        if ticket.created_by_id != user_id:
            raise TicketStatusException("Only the ticket creator can delete it")

        if ticket.status not in [TicketStatus.PENDING, TicketStatus.REJECTED]:
            raise TicketStatusException("Can only delete pending or rejected tickets")

        ticket.status = TicketStatus.CANCELLED
        await self.db.flush()
        return True

    # ============================================
    # Ticket List Operations
    # ============================================

    async def list_user_tickets(
        self, user_id: UUID, page: int = 1, size: int = 20, status_filter: Optional[TicketStatus] = None
    ) -> Tuple[List[Ticket], int]:
        """
        List tickets for a user (created or assigned).

        Args:
            user_id: User ID
            page: Page number
            size: Page size
            status_filter: Optional status filter

        Returns:
            Tuple of (tickets, total_count)
        """
        stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.creator),
                selectinload(Ticket.assignee),
                selectinload(Ticket.room),
            )
            .where(
                or_(Ticket.created_by_id == user_id, Ticket.assigned_to_id == user_id)
            )
        )

        if status_filter:
            stmt = stmt.where(Ticket.status == status_filter)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(Ticket.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        tickets = result.scalars().all()

        return list(tickets), total

    async def list_all_tickets(
        self,
        page: int = 1,
        size: int = 20,
        status_filter: Optional[TicketStatus] = None,
        domain_filter: Optional[str] = None,
        assignee_filter: Optional[UUID] = None,
    ) -> Tuple[List[Ticket], int]:
        """
        List all tickets (admin view).

        Args:
            page: Page number
            size: Page size
            status_filter: Optional status filter
            domain_filter: Optional domain filter
            assignee_filter: Optional assignee filter

        Returns:
            Tuple of (tickets, total_count)
        """
        stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.creator),
                selectinload(Ticket.assignee),
                selectinload(Ticket.room),
            )
        )

        if status_filter:
            stmt = stmt.where(Ticket.status == status_filter)
        if domain_filter:
            stmt = stmt.where(Ticket.domain == domain_filter)
        if assignee_filter:
            stmt = stmt.where(Ticket.assigned_to_id == assignee_filter)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(Ticket.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        tickets = result.scalars().all()

        return list(tickets), total

    # ============================================
    # Admin Ticket Operations
    # ============================================

    async def approve_ticket(self, ticket_id: UUID, admin_id: UUID) -> Ticket:
        """
        Approve a pending ticket.

        Args:
            ticket_id: Ticket ID
            admin_id: Admin user ID

        Returns:
            Approved ticket
        """
        ticket = await self.get_ticket_detail(ticket_id)

        if ticket.status != TicketStatus.PENDING:
            raise TicketStatusException("Only pending tickets can be approved")

        ticket.status = TicketStatus.APPROVED
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def reject_ticket(self, ticket_id: UUID, admin_id: UUID, reason: str) -> Ticket:
        """
        Reject a pending ticket.

        Args:
            ticket_id: Ticket ID
            admin_id: Admin user ID
            reason: Rejection reason

        Returns:
            Rejected ticket
        """
        ticket = await self.get_ticket_detail(ticket_id)

        if ticket.status != TicketStatus.PENDING:
            raise TicketStatusException("Only pending tickets can be rejected")

        ticket.status = TicketStatus.REJECTED
        ticket.rejection_reason = reason
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def assign_ticket(
        self, ticket_id: UUID, assignee_id: UUID, admin_id: UUID
    ) -> Ticket:
        """
        Assign ticket to a room agent.

        Args:
            ticket_id: Ticket ID
            assignee_id: Room agent user ID
            admin_id: Admin user ID

        Returns:
            Assigned ticket
        """
        ticket = await self.get_ticket_detail(ticket_id)

        if ticket.status not in [TicketStatus.APPROVED, TicketStatus.ASSIGNED]:
            raise TicketStatusException("Ticket must be approved before assignment")

        if ticket.assigned_to_id:
            raise TicketAlreadyAssignedException()

        # Verify assignee is a room agent
        stmt = select(User).where(User.id == assignee_id)
        result = await self.db.execute(stmt)
        assignee = result.scalar_one_or_none()

        if not assignee:
            raise UserNotFoundException()

        if UserRole.ROOM_AGENT not in assignee.role_names and UserRole.ADMIN not in assignee.role_names:
            raise TicketStatusException("Assignee must be a room agent or admin")

        ticket.status = TicketStatus.ASSIGNED
        ticket.assigned_to_id = assignee_id
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def update_ticket_admin(self, ticket_id: UUID, ticket_data: TicketAdminUpdate) -> Ticket:
        """
        Update ticket as admin.

        Args:
            ticket_id: Ticket ID
            ticket_data: Admin update data

        Returns:
            Updated ticket
        """
        ticket = await self.get_ticket_detail(ticket_id)

        update_data = ticket_data.model_dump(exclude_unset=True)

        # Handle status transitions
        if "status" in update_data:
            new_status = update_data.pop("status")
            if not self._is_valid_status_transition(ticket.status, new_status):
                raise TicketStatusException(
                    f"Invalid status transition from {ticket.status} to {new_status}"
                )
            ticket.status = new_status
            if new_status == TicketStatus.COMPLETED:
                ticket.completed_at = datetime.utcnow()

        # Apply remaining updates
        for field, value in update_data.items():
            setattr(ticket, field, value)

        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    def _is_valid_status_transition(self, current: TicketStatus, new: TicketStatus) -> bool:
        """Validate ticket status transition."""
        valid_transitions = {
            TicketStatus.PENDING: [TicketStatus.APPROVED, TicketStatus.REJECTED, TicketStatus.CANCELLED],
            TicketStatus.APPROVED: [TicketStatus.ASSIGNED, TicketStatus.REJECTED, TicketStatus.CANCELLED],
            TicketStatus.ASSIGNED: [TicketStatus.ACTIVE, TicketStatus.CANCELLED],
            TicketStatus.ACTIVE: [TicketStatus.COMPLETED, TicketStatus.CANCELLED],
            TicketStatus.REJECTED: [TicketStatus.CANCELLED],
            TicketStatus.COMPLETED: [],
            TicketStatus.CANCELLED: [],
        }
        return new in valid_transitions.get(current, [])

    # ============================================
    # Room Operations
    # ============================================

    async def create_room(self, creator_id: UUID, room_data: RoomCreate) -> Room:
        """
        Create a communication room.

        Args:
            creator_id: Creator user ID
            room_data: Room creation data

        Returns:
            Created room
        """
        room = Room(
            **room_data.model_dump(),
            created_by_id=creator_id,
        )
        self.db.add(room)
        await self.db.flush()

        # Add creator as member
        member = RoomMember(
            room_id=room.id,
            user_id=creator_id,
            role="moderator",
        )
        self.db.add(member)

        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def get_room_by_id(self, room_id: UUID) -> Optional[Room]:
        """Get room by ID with relationships loaded."""
        stmt = (
            select(Room)
            .options(
                selectinload(Room.creator),
                selectinload(Room.members).selectinload(RoomMember.user),
            )
            .where(Room.id == room_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_room_detail(self, room_id: UUID) -> Room:
        """Get room by ID or raise exception."""
        room = await self.get_room_by_id(room_id)
        if not room:
            raise RoomNotFoundException()
        return room

    async def update_room(self, room_id: UUID, room_data: RoomUpdate) -> Room:
        """
        Update room.

        Args:
            room_id: Room ID
            room_data: Update data

        Returns:
            Updated room
        """
        room = await self.get_room_detail(room_id)

        update_data = room_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(room, field, value)

        if "is_active" in update_data and update_data["is_active"] is False:
            room.closed_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(room)
        return room

    async def link_ticket_to_room(self, ticket_id: UUID, room_id: UUID) -> Ticket:
        """
        Link a ticket to a room.

        Args:
            ticket_id: Ticket ID
            room_id: Room ID

        Returns:
            Updated ticket
        """
        ticket = await self.get_ticket_detail(ticket_id)
        room = await self.get_room_detail(room_id)

        ticket.room_id = room_id
        ticket.status = TicketStatus.ACTIVE

        # Add ticket creator to room if not already member
        stmt = select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == ticket.created_by_id,
        )
        result = await self.db.execute(stmt)
        if not result.scalar_one_or_none():
            member = RoomMember(
                room_id=room_id,
                user_id=ticket.created_by_id,
                role="participant",
            )
            self.db.add(member)

        # Add assignee to room if exists
        if ticket.assigned_to_id:
            stmt = select(RoomMember).where(
                RoomMember.room_id == room_id,
                RoomMember.user_id == ticket.assigned_to_id,
            )
            result = await self.db.execute(stmt)
            if not result.scalar_one_or_none():
                member = RoomMember(
                    room_id=room_id,
                    user_id=ticket.assigned_to_id,
                    role="agent",
                )
                self.db.add(member)

        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    # ============================================
    # Room Member Operations
    # ============================================

    async def add_room_member(
        self, room_id: UUID, user_id: UUID, role: str = "participant"
    ) -> RoomMember:
        """
        Add a member to a room.

        Args:
            room_id: Room ID
            user_id: User ID to add
            role: Member role

        Returns:
            Created room member
        """
        room = await self.get_room_detail(room_id)

        # Check room capacity
        stmt = select(func.count()).select_from(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.is_active == True,
        )
        result = await self.db.execute(stmt)
        current_count = result.scalar() or 0

        if current_count >= room.max_participants:
            from app.core.exceptions import RoomFullException
            raise RoomFullException()

        # Check if already member
        stmt = select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.joined_at = datetime.utcnow()
                existing.role = role
                await self.db.flush()
                return existing
            return existing

        member = RoomMember(
            room_id=room_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_room_member(self, room_id: UUID, user_id: UUID) -> bool:
        """
        Remove a member from a room.

        Args:
            room_id: Room ID
            user_id: User ID to remove

        Returns:
            True if removed
        """
        stmt = select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
            RoomMember.is_active == True,
        )
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()

        if member:
            member.is_active = False
            member.left_at = datetime.utcnow()
            await self.db.flush()
            return True

        return False

    async def get_room_members(self, room_id: UUID) -> List[RoomMember]:
        """Get all active members of a room."""
        stmt = (
            select(RoomMember)
            .options(selectinload(RoomMember.user))
            .where(RoomMember.room_id == room_id, RoomMember.is_active == True)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def is_user_in_room(self, room_id: UUID, user_id: UUID) -> bool:
        """Check if user is an active member of a room."""
        stmt = select(RoomMember).where(
            RoomMember.room_id == room_id,
            RoomMember.user_id == user_id,
            RoomMember.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_user_rooms(
        self, user_id: UUID, page: int = 1, size: int = 20
    ) -> Tuple[List[Room], int]:
        """
        List rooms for a user.

        Args:
            user_id: User ID
            page: Page number
            size: Page size

        Returns:
            Tuple of (rooms, total_count)
        """
        stmt = (
            select(Room)
            .join(RoomMember, Room.id == RoomMember.room_id)
            .options(selectinload(Room.members).selectinload(RoomMember.user))
            .where(RoomMember.user_id == user_id, RoomMember.is_active == True)
        )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(Room.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(stmt)
        rooms = result.scalars().all()

        return list(rooms), total
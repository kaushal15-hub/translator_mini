from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base
def now(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    preferred_language: Mapped[str] = mapped_column(String(12), default="en")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    recipient: Mapped[str] = mapped_column(String(255), default="")
    domain: Mapped[str] = mapped_column(String(40), default="general")
    source_language: Mapped[str] = mapped_column(String(12))
    target_language: Mapped[str] = mapped_column(String(12))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="Pending", index=True)
    assigned_agent_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
class RoomMember(Base):
    __tablename__ = "room_members"
    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    __table_args__ = (Index("ix_room_member_unique", "room_id", "user_id", unique=True),)
class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    original_text: Mapped[str] = mapped_column(Text)
    translated_text: Mapped[str] = mapped_column(Text)
    source_language: Mapped[str] = mapped_column(String(12))
    target_language: Mapped[str] = mapped_column(String(12))
    domain: Mapped[str] = mapped_column(String(40))
    translation_mode: Mapped[str] = mapped_column(String(30), default="development-fallback")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class GlossaryDomain(Base):
    __tablename__ = "glossary_domains"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"
    id: Mapped[int] = mapped_column(primary_key=True)
    domain: Mapped[str] = mapped_column(String(40), index=True)
    term: Mapped[str] = mapped_column(String(255))
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    source_language: Mapped[str] = mapped_column(String(12), default="*")
    target_language: Mapped[str | None] = mapped_column(String(12), nullable=True)
    case_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    preserve_original: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(120))
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)

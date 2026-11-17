"""Initial schema migration

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    user_role_enum = postgresql.ENUM('user', 'admin', 'room_agent', name='userrole', create_type=True)
    user_role_enum.create(op.get_bind())

    user_status_enum = postgresql.ENUM('active', 'inactive', 'suspended', 'pending_verification', name='userstatus', create_type=True)
    user_status_enum.create(op.get_bind())

    ticket_status_enum = postgresql.ENUM('pending', 'approved', 'rejected', 'assigned', 'active', 'completed', 'cancelled', name='ticketstatus', create_type=True)
    ticket_status_enum.create(op.get_bind())

    ticket_priority_enum = postgresql.ENUM('low', 'normal', 'high', 'urgent', name='ticketpriority', create_type=True)
    ticket_priority_enum.create(op.get_bind())

    conversation_domain_enum = postgresql.ENUM('technology', 'medical', 'general', name='conversationdomain', create_type=True)
    conversation_domain_enum.create(op.get_bind())

    language_code_enum = postgresql.ENUM('en', 'kn', 'hi', 'ml', 'ta', name='languagecode', create_type=True)
    language_code_enum.create(op.get_bind())

    glossary_domain_enum = postgresql.ENUM('technology', 'medical', 'general', name='glossarydomain', create_type=True)
    glossary_domain_enum.create(op.get_bind())

    term_status_enum = postgresql.ENUM('active', 'inactive', 'deprecated', name='termstatus', create_type=True)
    term_status_enum.create(op.get_bind())

    audit_action_enum = postgresql.ENUM(
        'user_login', 'user_logout', 'user_register', 'user_password_change', 'user_profile_update',
        'admin_user_create', 'admin_user_update', 'admin_user_delete', 'admin_user_suspend', 'admin_user_activate',
        'admin_role_assign', 'admin_role_revoke',
        'ticket_create', 'ticket_update', 'ticket_approve', 'ticket_reject', 'ticket_assign', 'ticket_cancel', 'ticket_complete',
        'room_create', 'room_update', 'room_close', 'room_member_add', 'room_member_remove', 'room_member_role_change',
        'glossary_create', 'glossary_update', 'glossary_delete', 'glossary_import', 'glossary_term_create', 'glossary_term_update', 'glossary_term_delete',
        'security_failed_login', 'security_token_refresh', 'security_permission_denied', 'security_suspicious_activity',
        name='auditaction', create_type=True
    )
    audit_action_enum.create(op.get_bind())

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('preferred_language', sa.String(10), nullable=False, server_default='en'),
        sa.Column('status', user_status_enum, nullable=False, server_default='active'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_email_status', 'users', ['email', 'status'])

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_roles_name', 'roles', ['name'], unique=True)

    # Create user_roles association table
    op.create_table(
        'user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id'),
    )

    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False),
        sa.Column('jti', sa.String(36), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti'),
    )
    op.create_index('ix_refresh_tokens_user_expires', 'refresh_tokens', ['user_id', 'expires_at'])
    op.create_index('ix_refresh_tokens_jti', 'refresh_tokens', ['jti'], unique=True)

    # Create tickets table
    op.create_table(
        'tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', ticket_status_enum, nullable=False, server_default='pending'),
        sa.Column('priority', ticket_priority_enum, nullable=False, server_default='normal'),
        sa.Column('domain', conversation_domain_enum, nullable=False, server_default='general'),
        sa.Column('source_language', language_code_enum, nullable=False, server_default='en'),
        sa.Column('target_language', language_code_enum, nullable=False, server_default='kn'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tickets_status_created', 'tickets', ['status', 'created_at'])
    op.create_index('ix_tickets_creator_status', 'tickets', ['created_by_id', 'status'])
    op.create_index('ix_tickets_assignee_status', 'tickets', ['assigned_to_id', 'status'])

    # Create rooms table
    op.create_table(
        'rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('domain', conversation_domain_enum, nullable=False, server_default='general'),
        sa.Column('source_language', language_code_enum, nullable=False, server_default='en'),
        sa.Column('target_language', language_code_enum, nullable=False, server_default='kn'),
        sa.Column('max_participants', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_rooms_domain_active', 'rooms', ['domain', 'is_active'])

    # Create room_members table
    op.create_table(
        'room_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='participant'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id', 'user_id', name='uq_room_member'),
    )
    op.create_index('ix_room_members_room_user', 'room_members', ['room_id', 'user_id'])
    op.create_index('ix_room_members_user_active', 'room_members', ['user_id', 'is_active'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('room_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ticket_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('original_language', language_code_enum, nullable=False),
        sa.Column('translated_text', sa.Text(), nullable=True),
        sa.Column('translated_language', language_code_enum, nullable=True),
        sa.Column('domain', conversation_domain_enum, nullable=False),
        sa.Column('glossary_applied', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('protected_terms', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('translation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('delivery_status', sa.String(20), nullable=False, server_default='sent'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_messages_room_created', 'messages', ['room_id', 'created_at'])
    op.create_index('ix_messages_ticket_created', 'messages', ['ticket_id', 'created_at'])
    op.create_index('ix_messages_sender_created', 'messages', ['sender_id', 'created_at'])

    # Create glossaries table
    op.create_table(
        'glossaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('domain', glossary_domain_enum, nullable=False),
        sa.Column('source_language', language_code_enum, nullable=False),
        sa.Column('target_language', language_code_enum, nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(20), nullable=False, server_default='1.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('domain', 'source_language', 'target_language', name='uq_glossary_domain_langs'),
    )
    op.create_index('ix_glossaries_domain_active', 'glossaries', ['domain', 'is_active'])

    # Create glossary_terms table
    op.create_table(
        'glossary_terms',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('glossary_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_term', sa.String(500), nullable=False),
        sa.Column('alternatives', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('source_language', language_code_enum, nullable=False),
        sa.Column('target_language', language_code_enum, nullable=True),
        sa.Column('case_sensitive', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('preserve_original', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('status', term_status_enum, nullable=False, server_default='active'),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['glossary_id'], ['glossaries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_glossary_terms_glossary_original', 'glossary_terms', ['glossary_id', 'original_term'])
    op.create_index('ix_glossary_terms_glossary_status', 'glossary_terms', ['glossary_id', 'status'])
    op.create_index('ix_glossary_terms_original_priority', 'glossary_terms', ['original_term', 'priority'])

    # Create glossary_import_logs table
    op.create_table(
        'glossary_import_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('glossary_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_format', sa.String(20), nullable=False),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('imported_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['glossary_id'], ['glossaries.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['imported_by_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', audit_action_enum, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_type', sa.String(50), nullable=True),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_user_action', 'audit_logs', ['user_id', 'action'])
    op.create_index('ix_audit_logs_target', 'audit_logs', ['target_type', 'target_id'])
    op.create_index('ix_audit_logs_created_action', 'audit_logs', ['created_at', 'action'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('glossary_import_logs')
    op.drop_table('glossary_terms')
    op.drop_table('glossaries')
    op.drop_table('messages')
    op.drop_table('room_members')
    op.drop_table('rooms')
    op.drop_table('tickets')
    op.drop_table('refresh_tokens')
    op.drop_table('user_roles')
    op.drop_table('roles')
    op.drop_table('users')

    # Drop enum types
    postgresql.ENUM(name='auditaction').drop(op.get_bind())
    postgresql.ENUM(name='termstatus').drop(op.get_bind())
    postgresql.ENUM(name='glossarydomain').drop(op.get_bind())
    postgresql.ENUM(name='languagecode').drop(op.get_bind())
    postgresql.ENUM(name='conversationdomain').drop(op.get_bind())
    postgresql.ENUM(name='ticketpriority').drop(op.get_bind())
    postgresql.ENUM(name='ticketstatus').drop(op.get_bind())
    postgresql.ENUM(name='userstatus').drop(op.get_bind())
    postgresql.ENUM(name='userrole').drop(op.get_bind())
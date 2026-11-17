// API Type Definitions
// These mirror the backend Pydantic schemas

export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  full_name: string
  phone?: string
  avatar_url?: string
  preferred_language: string
  status: string
  is_superuser: boolean
  last_login?: string
  email_verified: boolean
  created_at: string
  updated_at: string
  roles: RoleResponse[]
}

export interface RoleResponse {
  id: string
  name: string
  display_name: string
  description?: string
  is_system: boolean
  created_at: string
  updated_at: string
}

export interface UserListResponse {
  users: UserResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export interface TicketResponse {
  id: string
  title: string
  description: string
  status: TicketStatus
  priority: TicketPriority
  domain: ConversationDomain
  source_language: LanguageCode
  target_language: LanguageCode
  created_by_id: string
  assigned_to_id?: string
  room_id?: string
  admin_notes?: string
  rejection_reason?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface TicketDetailResponse extends TicketResponse {
  creator_name?: string
  creator_email?: string
  assignee_name?: string
  assignee_email?: string
  room_name?: string
}

export interface TicketListResponse {
  tickets: TicketResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export type TicketStatus = 'pending' | 'approved' | 'rejected' | 'assigned' | 'active' | 'completed' | 'cancelled'
export type TicketPriority = 'low' | 'normal' | 'high' | 'urgent'
export type ConversationDomain = 'technology' | 'medical' | 'general'
export type LanguageCode = 'en' | 'kn' | 'hi' | 'ml' | 'ta'

export interface RoomResponse {
  id: string
  name: string
  description?: string
  domain: ConversationDomain
  source_language: LanguageCode
  target_language: LanguageCode
  max_participants: number
  is_active: boolean
  settings: Record<string, any>
  created_by_id: string
  created_at: string
  updated_at: string
  closed_at?: string
}

export interface RoomDetailResponse extends RoomResponse {
  creator_name?: string
  member_count: number
  members: RoomMemberResponse[]
}

export interface RoomMemberResponse {
  id: string
  room_id: string
  user_id: string
  role: string
  is_active: boolean
  joined_at: string
  left_at?: string
  user_name?: string
  user_email?: string
  user_preferred_language?: string
  permissions: Record<string, any>
}

export interface RoomListResponse {
  rooms: RoomResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export interface GlossaryResponse {
  id: string
  name: string
  domain: ConversationDomain
  source_language: LanguageCode
  target_language?: LanguageCode
  description?: string
  version: string
  is_active: boolean
  is_default: boolean
  created_by_id: string
  created_at: string
  updated_at: string
  term_count: number
}

export interface GlossaryDetailResponse extends GlossaryResponse {
  terms: GlossaryTermResponse[]
  creator_name?: string
}

export interface GlossaryListResponse {
  glossaries: GlossaryResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export interface GlossaryTermResponse {
  id: string
  glossary_id: string
  original_term: string
  alternatives: string[]
  aliases: string[]
  source_language: LanguageCode
  target_language?: LanguageCode
  case_sensitive: boolean
  preserve_original: boolean
  priority: number
  status: TermStatus
  context?: string
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface GlossaryTermListResponse {
  terms: GlossaryTermResponse[]
  total: number
  page: number
  size: number
  pages: number
}

export type TermStatus = 'active' | 'inactive' | 'deprecated'

export interface GlossaryImportResponse {
  success: boolean
  message: string
  glossary_id?: string
  total_rows: number
  successful_rows: number
  failed_rows: number
  errors?: Array<{ row: number; term: string; error: string }>
}

export interface MessageResponse {
  id: string
  room_id: string
  ticket_id?: string
  sender_id: string
  original_text: string
  original_language: LanguageCode
  translated_text?: string
  translated_language?: LanguageCode
  domain: ConversationDomain
  glossary_applied: boolean
  protected_terms?: Record<string, string>
  translation_metadata?: Record<string, any>
  delivery_status: string
  created_at: string
  updated_at: string
}

export interface TranslationResponse {
  original_text: string
  translated_text: string
  source_language: LanguageCode
  target_language: LanguageCode
  domain: ConversationDomain
  protected_terms: Record<string, string>
  translation_time_ms: number
  model_used: string
  glossary_applied: boolean
}

// WebSocket message types
export interface WSMessage {
  type: string
  [key: string]: any
}

export interface WSMessageMessage extends WSMessage {
  type: 'message'
  message: {
    id: string
    sender_id: string
    sender_name: string
    original_text: string
    original_language: LanguageCode
    translated_text: string
    translated_language: LanguageCode
    domain: ConversationDomain
    glossary_applied: boolean
    protected_terms: Record<string, string>
    timestamp: string
  }
}

export interface WSUserJoined extends WSMessage {
  type: 'user_joined'
  user_id: string
  user_name: string
  timestamp: string
}

export interface WSUserLeft extends WSMessage {
  type: 'user_left'
  user_id: string
  user_name: string
  timestamp: string
}

export interface WSTyping extends WSMessage {
  type: 'typing'
  user_id: string
  user_name: string
  is_typing: boolean
}

export interface WSError extends WSMessage {
  type: 'error'
  message: string
}

export type WSIncomingMessage =
  | { type: 'join_room'; room_id: string }
  | { type: 'leave_room' }
  | { type: 'send_message'; room_id: string; text: string }
  | { type: 'typing'; room_id: string; is_typing: boolean }
  | { type: 'ping' }

export type WSOutgoingMessage =
  | { type: 'connected'; user_id: string; user_name: string; connection_id: string; timestamp: string }
  | { type: 'join_room_response'; room_id: string; success: boolean }
  | { type: 'leave_room_response'; success: boolean }
  | WSMessageMessage
  | WSUserJoined
  | WSUserLeft
  | WSTyping
  | WSError
  | { type: 'pong'; timestamp: string }
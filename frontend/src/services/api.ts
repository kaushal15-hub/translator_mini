import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import type { Token } from '../types/api'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class ApiService {
  private client: AxiosInstance
  private refreshPromise: Promise<Token> | null = null

  constructor() {
    this.client = axios.create({
      baseURL: `${API_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor - add auth header
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token')
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const tokens = await this.refreshToken()
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${tokens.access_token}`
            }
            return this.client(originalRequest)
          } catch {
            // Refresh failed, redirect to login
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            window.location.href = '/login'
            return Promise.reject(error)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  setTokens(accessToken: string, refreshToken: string) {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }

  clearTokens() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // Auth endpoints
  async login(email: string, password: string, rememberMe = false): Promise<Token> {
    const response = await this.client.post<Token>('/auth/login', { email, password, remember_me: rememberMe })
    return response.data
  }

  async register(data: RegisterData): Promise<void> {
    await this.client.post('/auth/register', data)
  }

  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      await this.client.post('/auth/logout', { refresh_token: refreshToken })
    }
  }

  async refreshToken(): Promise<Token> {
    if (this.refreshPromise) {
      return this.refreshPromise
    }

    this.refreshPromise = (async () => {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        throw new Error('No refresh token')
      }

      const response = await this.client.post<Token>('/auth/refresh', { refresh_token: refreshToken })
      this.setTokens(response.data.access_token, response.data.refresh_token)
      return response.data
    })()

    try {
      return await this.refreshPromise
    } finally {
      this.refreshPromise = null
    }
  }

  async getCurrentUser(): Promise<UserResponse> {
    const response = await this.client.get<UserResponse>('/auth/me')
    return response.data
  }

  async updateProfile(data: Partial<UserResponse>): Promise<UserResponse> {
    const response = await this.client.put<UserResponse>('/auth/me', data)
    return response.data
  }

  async changePassword(data: { current_password: string; new_password: string }): Promise<void> {
    await this.client.put('/auth/me/password', data)
  }

  // Ticket endpoints
  async createTicket(data: CreateTicketData): Promise<TicketResponse> {
    const response = await this.client.post<TicketResponse>('/tickets', data)
    return response.data
  }

  async getTickets(params?: TicketListParams): Promise<TicketListResponse> {
    const response = await this.client.get<TicketListResponse>('/tickets', { params })
    return response.data
  }

  async getTicket(ticketId: string): Promise<TicketDetailResponse> {
    const response = await this.client.get<TicketDetailResponse>(`/tickets/${ticketId}`)
    return response.data
  }

  async updateTicket(ticketId: string, data: Partial<CreateTicketData>): Promise<TicketResponse> {
    const response = await this.client.put<TicketResponse>(`/tickets/${ticketId}`, data)
    return response.data
  }

  async cancelTicket(ticketId: string): Promise<void> {
    await this.client.delete(`/tickets/${ticketId}`)
  }

  // Admin ticket endpoints
  async getAllTickets(params?: AdminTicketListParams): Promise<TicketListResponse> {
    const response = await this.client.get<TicketListResponse>('/tickets/admin/all', { params })
    return response.data
  }

  async approveTicket(ticketId: string): Promise<TicketResponse> {
    const response = await this.client.post<TicketResponse>(`/tickets/${ticketId}/approve`)
    return response.data
  }

  async rejectTicket(ticketId: string, reason: string): Promise<TicketResponse> {
    const response = await this.client.post<TicketResponse>(`/tickets/${ticketId}/reject`, { reason })
    return response.data
  }

  async assignTicket(ticketId: string, assigneeId: string): Promise<TicketResponse> {
    const response = await this.client.post<TicketResponse>(`/tickets/${ticketId}/assign`, { assignee_id: assigneeId })
    return response.data
  }

  async updateTicketAdmin(ticketId: string, data: AdminTicketUpdateData): Promise<TicketResponse> {
    const response = await this.client.put<TicketResponse>(`/tickets/${ticketId}/admin`, data)
    return response.data
  }

  // Room endpoints
  async createRoom(ticketId: string, data: CreateRoomData): Promise<RoomResponse> {
    const response = await this.client.post<RoomResponse>(`/tickets/${ticketId}/room`, data)
    return response.data
  }

  async getMyRooms(params?: RoomListParams): Promise<RoomListResponse> {
    const response = await this.client.get<RoomListResponse>('/tickets/rooms/my', { params })
    return response.data
  }

  async getRoom(roomId: string): Promise<RoomDetailResponse> {
    const response = await this.client.get<RoomDetailResponse>(`/tickets/rooms/${roomId}`)
    return response.data
  }

  async updateRoom(roomId: string, data: Partial<CreateRoomData>): Promise<RoomResponse> {
    const response = await this.client.put<RoomResponse>(`/tickets/rooms/${roomId}`, data)
    return response.data
  }

  async addRoomMember(roomId: string, data: AddRoomMemberData): Promise<RoomMemberResponse> {
    const response = await this.client.post<RoomMemberResponse>(`/tickets/rooms/${roomId}/members`, data)
    return response.data
  }

  async removeRoomMember(roomId: string, userId: string): Promise<void> {
    await this.client.delete(`/tickets/rooms/${roomId}/members/${userId}`)
  }

  async getRoomMembers(roomId: string): Promise<RoomMemberResponse[]> {
    const response = await this.client.get<RoomMemberResponse[]>(`/tickets/rooms/${roomId}/members`)
    return response.data
  }

  // Glossary endpoints
  async createGlossary(data: CreateGlossaryData): Promise<GlossaryResponse> {
    const response = await this.client.post<GlossaryResponse>('/glossaries', data)
    return response.data
  }

  async getGlossaries(params?: GlossaryListParams): Promise<GlossaryListResponse> {
    const response = await this.client.get<GlossaryListResponse>('/glossaries', { params })
    return response.data
  }

  async getGlossary(glossaryId: string): Promise<GlossaryDetailResponse> {
    const response = await this.client.get<GlossaryDetailResponse>(`/glossaries/${glossaryId}`)
    return response.data
  }

  async updateGlossary(glossaryId: string, data: Partial<CreateGlossaryData>): Promise<GlossaryResponse> {
    const response = await this.client.put<GlossaryResponse>(`/glossaries/${glossaryId}`, data)
    return response.data
  }

  async deleteGlossary(glossaryId: string): Promise<void> {
    await this.client.delete(`/glossaries/${glossaryId}`)
  }

  async importGlossary(file: File, data: ImportGlossaryData): Promise<GlossaryImportResponse> {
    const formData = new FormData()
    formData.append('file', file)
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined) {
        formData.append(key, String(value))
      }
    })

    const response = await this.client.post<GlossaryImportResponse>('/glossaries/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  }

  async getGlossaryTerms(glossaryId: string, params?: TermListParams): Promise<GlossaryTermListResponse> {
    const response = await this.client.get<GlossaryTermListResponse>(`/glossaries/${glossaryId}/terms`, { params })
    return response.data
  }

  async createGlossaryTerm(glossaryId: string, data: CreateTermData): Promise<GlossaryTermResponse> {
    const response = await this.client.post<GlossaryTermResponse>(`/glossaries/${glossaryId}/terms`, data)
    return response.data
  }

  async updateGlossaryTerm(glossaryId: string, termId: string, data: Partial<CreateTermData>): Promise<GlossaryTermResponse> {
    const response = await this.client.put<GlossaryTermResponse>(`/glossaries/${glossaryId}/terms/${termId}`, data)
    return response.data
  }

  async deleteGlossaryTerm(glossaryId: string, termId: string): Promise<void> {
    await this.client.delete(`/glossaries/${glossaryId}/terms/${termId}`)
  }

  // User management (admin)
  async getUsers(params?: UserListParams): Promise<UserListResponse> {
    const response = await this.client.get<UserListResponse>('/auth/users', { params })
    return response.data
  }

  async getUser(userId: string): Promise<UserResponse> {
    const response = await this.client.get<UserResponse>(`/auth/users/${userId}`)
    return response.data
  }

  async createUser(data: CreateUserData): Promise<UserResponse> {
    const response = await this.client.post<UserResponse>('/auth/users', data)
    return response.data
  }

  async updateUser(userId: string, data: AdminUserUpdateData): Promise<UserResponse> {
    const response = await this.client.put<UserResponse>(`/auth/users/${userId}`, data)
    return response.data
  }

  async deleteUser(userId: string): Promise<void> {
    await this.client.delete(`/auth/users/${userId}`)
  }

  // Roles
  async getRoles(): Promise<RoleResponse[]> {
    const response = await this.client.get<RoleResponse[]>('/auth/roles')
    return response.data
  }

  async createRole(data: CreateRoleData): Promise<RoleResponse> {
    const response = await this.client.post<RoleResponse>('/auth/roles', data)
    return response.data
  }
}

// Type definitions for API
interface RegisterData {
  email: string
  password: string
  full_name: string
  phone?: string
  preferred_language: string
}

interface CreateTicketData {
  title: string
  description: string
  priority: 'low' | 'normal' | 'high' | 'urgent'
  domain: 'technology' | 'medical' | 'general'
  source_language: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  target_language: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
}

interface TicketListParams {
  page?: number
  size?: number
  status_filter?: string
}

interface TicketListResponse {
  tickets: TicketResponse[]
  total: number
  page: number
  size: number
  pages: number
}

interface TicketResponse {
  id: string
  title: string
  description: string
  status: string
  priority: string
  domain: string
  source_language: string
  target_language: string
  created_by_id: string
  assigned_to_id?: string
  room_id?: string
  admin_notes?: string
  rejection_reason?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

interface TicketDetailResponse extends TicketResponse {
  creator_name?: string
  creator_email?: string
  assignee_name?: string
  assignee_email?: string
  room_name?: string
}

interface AdminTicketListParams extends TicketListParams {
  domain_filter?: string
  assignee_filter?: string
}

interface AdminTicketUpdateData {
  status?: string
  priority?: string
  domain?: string
  source_language?: string
  target_language?: string
  assigned_to_id?: string
  admin_notes?: string
  rejection_reason?: string
}

interface CreateRoomData {
  name: string
  description?: string
  domain: 'technology' | 'medical' | 'general'
  source_language: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  target_language: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  max_participants?: number
}

interface RoomListParams {
  page?: number
  size?: number
}

interface RoomListResponse {
  rooms: RoomResponse[]
  total: number
  page: number
  size: number
  pages: number
}

interface RoomResponse {
  id: string
  name: string
  description?: string
  domain: string
  source_language: string
  target_language: string
  max_participants: number
  is_active: boolean
  settings: Record<string, any>
  created_by_id: string
  created_at: string
  updated_at: string
  closed_at?: string
}

interface RoomDetailResponse extends RoomResponse {
  creator_name?: string
  member_count: number
  members: RoomMemberResponse[]
}

interface RoomMemberResponse {
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

interface AddRoomMemberData {
  user_id: string
  role?: string
  permissions?: Record<string, any>
}

interface GlossaryListParams {
  page?: number
  size?: number
  domain_filter?: string
  active_only?: boolean
}

interface GlossaryListResponse {
  glossaries: GlossaryResponse[]
  total: number
  page: number
  size: number
  pages: number
}

interface GlossaryResponse {
  id: string
  name: string
  domain: string
  source_language: string
  target_language?: string
  description?: string
  version: string
  is_active: boolean
  is_default: boolean
  created_by_id: string
  created_at: string
  updated_at: string
  term_count: number
}

interface GlossaryDetailResponse extends GlossaryResponse {
  terms: GlossaryTermResponse[]
  creator_name?: string
}

interface CreateGlossaryData {
  name: string
  domain: 'technology' | 'medical' | 'general'
  source_language: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  target_language?: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  description?: string
  version?: string
  is_default?: boolean
}

interface ImportGlossaryData {
  domain: 'technology' | 'medical' | 'general'
  source_language: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  target_language?: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  name?: string
  overwrite?: boolean
  glossary_id?: string
}

interface GlossaryImportResponse {
  success: boolean
  message: string
  glossary_id?: string
  total_rows: number
  successful_rows: number
  failed_rows: number
  errors?: Array<{ row: number; term: string; error: string }>
}

interface TermListParams {
  page?: number
  size?: number
  status_filter?: string
  search?: string
}

interface GlossaryTermListResponse {
  terms: GlossaryTermResponse[]
  total: number
  page: number
  size: number
  pages: number
}

interface GlossaryTermResponse {
  id: string
  glossary_id: string
  original_term: string
  alternatives: string[]
  aliases: string[]
  source_language: string
  target_language?: string
  case_sensitive: boolean
  preserve_original: boolean
  priority: number
  status: string
  context?: string
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

interface CreateTermData {
  original_term: string
  alternatives?: string[]
  aliases?: string[]
  source_language: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  target_language?: 'en' | 'kn' | 'hi' | 'ml' | 'ta'
  case_sensitive?: boolean
  preserve_original?: boolean
  priority?: number
  status?: 'active' | 'inactive' | 'deprecated'
  context?: string
  metadata?: Record<string, any>
}

interface UserListParams {
  page?: number
  size?: number
  search?: string
}

interface UserListResponse {
  users: UserResponse[]
  total: number
  page: number
  size: number
  pages: number
}

interface UserResponse {
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

interface CreateUserData {
  email: string
  password: string
  full_name: string
  phone?: string
  preferred_language: string
  role_names?: string[]
}

interface AdminUserUpdateData {
  full_name?: string
  phone?: string
  preferred_language?: string
  status?: string
  is_superuser?: boolean
  roles?: string[]
}

interface RoleResponse {
  id: string
  name: string
  display_name: string
  description?: string
  is_system: boolean
  created_at: string
  updated_at: string
}

interface CreateRoleData {
  name: string
  display_name: string
  description?: string
}

export const api = new ApiService()
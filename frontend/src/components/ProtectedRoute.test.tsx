import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'
import ProtectedRoute from './ProtectedRoute'
import { AuthProvider, useAuth } from '../context/AuthContext'
import { ReactNode } from 'react'

// Mock useAuth
vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: ReactNode }) => children,
}))

const mockUseAuth = useAuth as vi.Mock

function renderWithRouter(ui: ReactNode) {
  return render(
    <BrowserRouter>
      {ui}
    </BrowserRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders children when user is authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: { id: '1', email: 'test@example.com', full_name: 'Test User', roles: [] },
      loading: false,
    })

    renderWithRouter(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('shows loading state when auth is loading', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: true,
    })

    renderWithRouter(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('redirects to login when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
    })

    renderWithRouter(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )

    // Should redirect to /login
    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
  })

  it('allows admin access when requiredRole is admin', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: '1',
        email: 'admin@example.com',
        full_name: 'Admin User',
        roles: [{ name: 'admin', display_name: 'Admin' }],
        is_superuser: false,
      },
      loading: false,
    })

    renderWithRouter(
      <ProtectedRoute requiredRole="admin">
        <div data-testid="admin-content">Admin Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByTestId('admin-content')).toBeInTheDocument()
  })

  it('denies admin access for non-admin users', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: '1',
        email: 'user@example.com',
        full_name: 'Regular User',
        roles: [{ name: 'user', display_name: 'User' }],
        is_superuser: false,
      },
      loading: false,
    })

    renderWithRouter(
      <ProtectedRoute requiredRole="admin">
        <div data-testid="admin-content">Admin Content</div>
      </ProtectedRoute>
    )

    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument()
  })

  it('allows superuser access to admin routes', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: '1',
        email: 'super@example.com',
        full_name: 'Super User',
        roles: [],
        is_superuser: true,
      },
      loading: false,
    })

    renderWithRouter(
      <ProtectedRoute requiredRole="admin">
        <div data-testid="admin-content">Admin Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByTestId('admin-content')).toBeInTheDocument()
  })

  it('allows room_agent access when requiredRole is room_agent', () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: '1',
        email: 'agent@example.com',
        full_name: 'Room Agent',
        roles: [{ name: 'room_agent', display_name: 'Room Agent' }],
        is_superuser: false,
      },
      loading: false,
    })

    renderWithRouter(
      <ProtectedRoute requiredRole="room_agent">
        <div data-testid="agent-content">Agent Content</div>
      </ProtectedRoute>
    )

    expect(screen.getByTestId('agent-content')).toBeInTheDocument()
  })
})
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ReactNode } from 'react'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: 'admin' | 'room_agent'
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check role requirement
  if (requiredRole) {
    const userRoles = user.roles?.map(r => r.name) || []
    const isAdmin = user.is_superuser || userRoles.includes('admin')
    const isRoomAgent = userRoles.includes('room_agent')

    if (requiredRole === 'admin' && !isAdmin) {
      return <Navigate to="/dashboard" replace />
    }

    if (requiredRole === 'room_agent' && !isAdmin && !isRoomAgent) {
      return <Navigate to="/dashboard" replace />
    }
  }

  return <>{children}</>
}
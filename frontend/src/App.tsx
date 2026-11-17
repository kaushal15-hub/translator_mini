import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import CreateTicket from './pages/CreateTicket'
import TicketHistory from './pages/TicketHistory'
import CommunicationRoom from './pages/CommunicationRoom'
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminTickets from './pages/admin/AdminTickets'
import AdminRooms from './pages/admin/AdminRooms'
import AdminUsers from './pages/admin/AdminUsers'
import AdminGlossaries from './pages/admin/AdminGlossaries'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <Register />} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/tickets/create" element={<CreateTicket />} />
        <Route path="/tickets/history" element={<TicketHistory />} />
        <Route path="/rooms/:roomId" element={<CommunicationRoom />} />

        {/* Admin routes */}
        <Route element={<ProtectedRoute requiredRole="admin"><Layout /></ProtectedRoute>}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/tickets" element={<AdminTickets />} />
          <Route path="/admin/rooms" element={<AdminRooms />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/admin/glossaries" element={<AdminGlossaries />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
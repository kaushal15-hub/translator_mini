import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Menu, X, LogOut, LayoutDashboard, TicketPlus, History, Users, Settings, BookOpen, Shield, Home } from 'lucide-react'
import { useState } from 'react'
import { cn } from '../utils/cn'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/tickets/create', label: 'Create Ticket', icon: TicketPlus },
    { path: '/tickets/history', label: 'Ticket History', icon: History },
  ]

  const adminNavItems = [
    { path: '/admin', label: 'Admin Dashboard', icon: LayoutDashboard },
    { path: '/admin/tickets', label: 'Manage Tickets', icon: Shield },
    { path: '/admin/rooms', label: 'Manage Rooms', icon: Users },
    { path: '/admin/users', label: 'Manage Users', icon: Users },
    { path: '/admin/glossaries', label: 'Glossaries', icon: BookOpen },
  ]

  const isAdmin = user?.is_superuser || user?.roles?.some(r => r.name === 'admin')

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full w-64 bg-card border-r border-border',
          'transform transition-transform duration-300 ease-in-out lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-4 border-b border-border">
            <NavLink to="/dashboard" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
                <BookOpen className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-semibold text-lg">Translator</span>
            </NavLink>
            <button
              className="lg:hidden p-2 rounded-md hover:bg-accent"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Navigation
            </div>
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                  )
                }
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </NavLink>
            ))}

            {isAdmin && (
              <>
                <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Administration
                </div>
                {adminNavItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                      )
                    }
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="h-5 w-5" />
                    {item.label}
                  </NavLink>
                ))}
              </>
            )}
          </nav>

          {/* User info */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
                {user?.full_name?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.full_name}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 px-4 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border">
          <button
            className="lg:hidden p-2 rounded-md hover:bg-accent"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-6 w-6" />
          </button>

          <div className="flex-1" />

          {/* Connection status */}
          <ConnectionIndicator />

          {/* User menu */}
          <div className="relative">
            <button
              className="flex items-center gap-2 p-2 rounded-lg hover:bg-accent"
              onClick={() => setUserMenuOpen(!userMenuOpen)}
            >
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
                {user?.full_name?.charAt(0).toUpperCase()}
              </div>
              <span className="hidden sm:block text-sm font-medium">{user?.full_name}</span>
            </button>

            {userMenuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
                <div className="absolute right-0 top-full z-50 mt-2 w-48 rounded-md bg-card border border-border shadow-lg py-1">
                  <NavLink
                    to="/dashboard"
                    className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-accent"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <Home className="h-4 w-4" />
                    Dashboard
                  </NavLink>
                  <NavLink
                    to="/tickets/history"
                    className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-accent"
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <History className="h-4 w-4" />
                    My Tickets
                  </NavLink>
                  <div className="border-t border-border my-1" />
                  <button
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm text-destructive hover:bg-accent"
                    onClick={handleLogout}
                  >
                    <LogOut className="h-4 w-4" />
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

// Connection indicator component
function ConnectionIndicator() {
  // In a real app, this would connect to WebSocket status
  return (
    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-accent">
      <span className="connection-indicator connected" />
      <span className="text-xs text-muted-foreground">Connected</span>
    </div>
  )
}
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { TicketPlus, Users, MessageSquare, BookOpen, Shield, TrendingUp, Loader2 } from 'lucide-react'
import { api } from '../../services/api'
import { cn } from '../../utils/cn'
import { formatDistanceToNow } from 'date-fns'

const stats = [
  {
    label: 'Total Tickets',
    value: 0,
    icon: TicketPlus,
    color: 'text-blue-500',
    bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    link: '/admin/tickets',
  },
  {
    label: 'Active Rooms',
    value: 0,
    icon: MessageSquare,
    color: 'text-green-500',
    bgColor: 'bg-green-100 dark:bg-green-900/30',
    link: '/admin/rooms',
  },
  {
    label: 'Total Users',
    value: 0,
    icon: Users,
    color: 'text-purple-500',
    bgColor: 'bg-purple-100 dark:bg-purple-900/30',
    link: '/admin/users',
  },
  {
    label: 'Glossaries',
    value: 0,
    icon: BookOpen,
    color: 'text-orange-500',
    bgColor: 'bg-orange-100 dark:bg-orange-900/30',
    link: '/admin/glossaries',
  },
]

export default function AdminDashboard() {
  const { data: ticketsResponse } = useQuery({
    queryKey: ['admin-tickets'],
    queryFn: () => api.getAllTickets({ size: 1 }),
  })

  const { data: usersResponse } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api.getUsers({ size: 1 }),
  })

  const { data: glossariesResponse } = useQuery({
    queryKey: ['admin-glossaries'],
    queryFn: () => api.getGlossaries({ size: 1 }),
  })

  const { data: roomsResponse } = useQuery({
    queryKey: ['admin-rooms'],
    queryFn: () => api.getMyRooms({ size: 1 }), // Need admin rooms endpoint
  })

  const updatedStats = stats.map(s => ({
    ...s,
    value: s.label === 'Total Tickets' ? ticketsResponse?.total || 0 :
           s.label === 'Active Rooms' ? roomsResponse?.rooms.filter(r => r.is_active).length || 0 :
           s.label === 'Total Users' ? usersResponse?.total || 0 :
           glossariesResponse?.total || 0,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <p className="text-muted-foreground">System overview and management</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {updatedStats.map((stat) => (
          <Link key={stat.label} to={stat.link} className="block">
            <div className="p-4 rounded-xl border border-border bg-card hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-3xl font-bold">{stat.value}</p>
                </div>
                <div className={cn('p-3 rounded-xl', stat.bgColor)}>
                  <stat.icon className={cn('h-6 w-6', stat.color)} />
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Link to="/admin/tickets" className="p-4 rounded-xl border border-border hover:bg-accent transition-colors text-center">
            <Shield className="h-10 w-10 mx-auto mb-2 text-blue-500" />
            <p className="font-medium">Manage Tickets</p>
            <p className="text-sm text-muted-foreground">Review and approve tickets</p>
          </Link>
          <Link to="/admin/rooms" className="p-4 rounded-xl border border-border hover:bg-accent transition-colors text-center">
            <MessageSquare className="h-10 w-10 mx-auto mb-2 text-green-500" />
            <p className="font-medium">Manage Rooms</p>
            <p className="text-sm text-muted-foreground">View and configure rooms</p>
          </Link>
          <Link to="/admin/users" className="p-4 rounded-xl border border-border hover:bg-accent transition-colors text-center">
            <Users className="h-10 w-10 mx-auto mb-2 text-purple-500" />
            <p className="font-medium">Manage Users</p>
            <p className="text-sm text-muted-foreground">User accounts and roles</p>
          </Link>
          <Link to="/admin/glossaries" className="p-4 rounded-xl border border-border hover:bg-accent transition-colors text-center">
            <BookOpen className="h-10 w-10 mx-auto mb-2 text-orange-500" />
            <p className="font-medium">Manage Glossaries</p>
            <p className="text-sm text-muted-foreground">Terminology and domains</p>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="rounded-xl border border-border bg-card">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-semibold">Recent Tickets</h2>
        </div>
        <div className="divide-y divide-border">
          {ticketsResponse?.tickets.slice(0, 5).map((ticket: any) => (
            <Link
              key={ticket.id}
              to="/admin/tickets"
              className="p-4 hover:bg-accent transition-colors flex items-center justify-between"
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{ticket.title}</p>
                <p className="text-sm text-muted-foreground truncate">{ticket.description}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                  <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                    {ticket.domain}
                  </span>
                  <span>{formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}</span>
                </div>
              </div>
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                {ticket.status}
              </span>
            </Link>
          ))}
          {(!ticketsResponse?.tickets.length) && (
            <div className="p-8 text-center text-muted-foreground">
              <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No tickets yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
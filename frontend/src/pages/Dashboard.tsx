import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { TicketPlus, History, Users, MessageSquare, Clock, CheckCircle, XCircle, AlertTriangle, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import type { TicketResponse, RoomResponse } from '../types/api'
import { cn } from '../utils/cn'
import { formatDistanceToNow } from 'date-fns'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  assigned: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  completed: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
  cancelled: 'bg-gray-100 text-gray-600 dark:bg-gray-900/30 dark:text-gray-500',
}

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'pending': return <Clock className='h-3 w-3 mr-1' />
    case 'approved': return <CheckCircle className='h-3 w-3 mr-1' />
    case 'rejected': return <XCircle className='h-3 w-3 mr-1' />
    case 'assigned': return <AlertTriangle className='h-3 w-3 mr-1' />
    case 'active': return <MessageSquare className='h-3 w-3 mr-1' />
    case 'completed': return <CheckCircle className='h-3 w-3 mr-1' />
    case 'cancelled': return <XCircle className='h-3 w-3 mr-1' />
    default: return <Clock className='h-3 w-3 mr-1' />
  }
}

export default function Dashboard() {
  const { data: ticketsResponse, isLoading: ticketsLoading } = useQuery({
    queryKey: ['my-tickets'],
    queryFn: () => api.getTickets({ size: 5 }),
  })

  const { data: roomsResponse, isLoading: roomsLoading } = useQuery({
    queryKey: ['my-rooms'],
    queryFn: () => api.getMyRooms({ size: 5 }),
  })

  const stats = [
    {
      label: 'My Tickets',
      value: ticketsResponse?.total || 0,
      icon: TicketPlus,
      color: 'text-blue-500',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
      link: '/tickets/history',
    },
    {
      label: 'Active Rooms',
      value: roomsResponse?.rooms.filter(r => r.is_active).length || 0,
      icon: MessageSquare,
      color: 'text-green-500',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
      link: '/tickets/history',
    },
    {
      label: 'Pending Tickets',
      value: ticketsResponse?.tickets.filter(t => t.status === 'pending').length || 0,
      icon: Clock,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
      link: '/tickets/history',
    },
    {
      label: 'Completed',
      value: ticketsResponse?.tickets.filter(t => t.status === 'completed').length || 0,
      icon: CheckCircle,
      color: 'text-gray-500',
      bgColor: 'bg-gray-100 dark:bg-gray-900/30',
      link: '/tickets/history',
    },
  ]

  return (
    <div className='space-y-6'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h1 className='text-2xl font-bold'>Dashboard</h1>
          <p className='text-muted-foreground'>Overview of your communication activities</p>
        </div>
        <Link
          to='/tickets/create'
          className='inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors'
        >
          <TicketPlus className='h-4 w-4' />
          Create Ticket
        </Link>
      </div>

      <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
        {stats.map((stat) => (
          <Link key={stat.label} to={stat.link} className='block'>
            <div className='p-4 rounded-xl border border-border bg-card hover:shadow-md transition-shadow'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-muted-foreground'>{stat.label}</p>
                  <p className='text-3xl font-bold'>{stat.value}</p>
                </div>
                <div className={cn('p-3 rounded-xl', stat.bgColor)}>
                  <stat.icon className={cn('h-6 w-6', stat.color)} />
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className='grid gap-6 lg:grid-cols-2'>
        <div className='rounded-xl border border-border bg-card'>
          <div className='p-4 border-b border-border flex items-center justify-between'>
            <h2 className='text-lg font-semibold'>Recent Tickets</h2>
            <Link to='/tickets/history' className='text-sm text-primary hover:underline'>
              View all
            </Link>
          </div>
          <div className='divide-y divide-border'>
            {ticketsLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className='p-4 animate-pulse'>
                  <div className='h-4 bg-muted rounded w-3/4 mb-2' />
                  <div className='h-3 bg-muted rounded w-1/2' />
                </div>
              ))
            ) : ticketsResponse?.tickets.length === 0 ? (
              <div className='p-8 text-center text-muted-foreground'>
                <TicketPlus className='h-12 w-12 mx-auto mb-4 opacity-50' />
                <p>No tickets yet</p>
                <Link to='/tickets/create' className='text-primary hover:underline mt-2 inline-block'>
                  Create your first ticket
                </Link>
              </div>
            ) : (
              ticketsResponse?.tickets.map((ticket) => (
                <Link
                  key={ticket.id}
                  to='/tickets/history'
                  className='block p-4 hover:bg-accent transition-colors'
                >
                  <div className='flex items-start justify-between gap-4'>
                    <div className='flex-1 min-w-0'>
                      <h3 className='font-medium truncate'>{ticket.title}</h3>
                      <p className='text-sm text-muted-foreground truncate mt-1'>
                        {ticket.description}
                      </p>
                      <div className='flex items-center gap-2 mt-2 text-xs text-muted-foreground'>
                        <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', statusColors[ticket.status])}>
                          <StatusIcon status={ticket.status} />
                          {ticket.status}
                        </span>
                        <span>{formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>

        <div className='rounded-xl border border-border bg-card'>
          <div className='p-4 border-b border-border flex items-center justify-between'>
            <h2 className='text-lg font-semibold'>Active Rooms</h2>
            <Link to='/tickets/history' className='text-sm text-primary hover:underline'>
              View all
            </Link>
          </div>
          <div className='divide-y divide-border'>
            {roomsLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className='p-4 animate-pulse'>
                  <div className='h-4 bg-muted rounded w-3/4 mb-2' />
                  <div className='h-3 bg-muted rounded w-1/2' />
                </div>
              ))
            ) : roomsResponse?.rooms.length === 0 ? (
              <div className='p-8 text-center text-muted-foreground'>
                <MessageSquare className='h-12 w-12 mx-auto mb-4 opacity-50' />
                <p>No active rooms</p>
                <p className='text-sm'>Create a ticket to start communicating</p>
              </div>
            ) : (
              roomsResponse?.rooms.map((room) => (
                <Link
                  key={room.id}
                  to={/rooms/}
                  className='block p-4 hover:bg-accent transition-colors'
                >
                  <div className='flex items-center justify-between gap-4'>
                    <div className='flex-1 min-w-0'>
                      <div className='flex items-center gap-2'>
                        <h3 className='font-medium truncate'>{room.name}</h3>
                        <span className='px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary'>
                          {room.domain}
                        </span>
                      </div>
                      <p className='text-sm text-muted-foreground truncate mt-1'>
                        {room.source_language} → {room.target_language}
                      </p>
                      <div className='flex items-center gap-2 mt-2 text-xs text-muted-foreground'>
                        <span>{room.member_count || 0} participants</span>
                        <span>•</span>
                        <span>{formatDistanceToNow(new Date(room.updated_at), { addSuffix: true })}</span>
                      </div>
                    </div>
                    <span className='px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'>
                      Active
                    </span>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>

      <div className='rounded-xl border border-border bg-card p-6'>
        <h2 className='text-lg font-semibold mb-4'>Quick Actions</h2>
        <div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'>
          <Link to='/tickets/create' className='p-4 rounded-xl border border-border hover:bg-accent transition-colors text-center'>
            <TicketPlus className='h-10 w-10 mx-auto mb-2 text-primary' />
            <p className='font-medium'>Create Ticket</p>
            <p className='text-sm text-muted-foreground'>Start new communication</p>
          </Link>
          <Link to='/tickets/history' className='p-4 rounded-xl border border-border hover:bg-accent transition-colors text-center'>
            <History className='h-10 w-10 mx-auto mb-2 text-blue-500' />
            <p className='font-medium'>View History</p>
            <p className='text-sm text-muted-foreground'>See all your tickets</p>
          </Link>
          <Link to='/tickets/history' className='p-4 rounded-xl border border-border hover:bg-accent transition-colors text-center'>
            <MessageSquare className='h-10 w-10 mx-auto mb-2 text-green-500' />
            <p className='font-medium'>My Rooms</p>
            <p className='text-sm text-muted-foreground'>Access communication rooms</p>
          </Link>
          <Link to='/tickets/history' className='p-4 rounded-xl border border-border hover:bg-accent transition-colors text-center'>
            <Users className='h-10 w-10 mx-auto mb-2 text-purple-500' />
            <p className='font-medium'>Contacts</p>
            <p className='text-sm text-muted-foreground'>Manage connections</p>
          </Link>
        </div>
      </div>
    </div>
  )
}
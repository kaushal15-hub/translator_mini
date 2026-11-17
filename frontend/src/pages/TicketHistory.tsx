import { useState } from 'react'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Search, Filter, ChevronDown, Loader2, Clock, CheckCircle, XCircle, AlertTriangle, MessageSquare, TicketPlus } from 'lucide-react'
import { api } from '../services/api'
import type { TicketResponse, TicketListResponse, TicketStatus } from '../types/api'
import { cn } from '../utils/cn'
import { formatDistanceToNow, format } from 'date-fns'

const statusColors: Record<TicketStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  approved: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  rejected: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  assigned: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  completed: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
  cancelled: 'bg-gray-100 text-gray-600 dark:bg-gray-900/30 dark:text-gray-500',
}

const StatusIcon = ({ status }: { status: TicketStatus }) => {
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

export default function TicketHistory() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<TicketStatus | 'all'>('all')
  const [debouncedSearch, setDebouncedSearch] = useState('')

  const { data: ticketsResponse, isLoading, isFetching } = useQuery({
    queryKey: ['my-tickets', page, debouncedSearch, statusFilter],
    queryFn: () => api.getTickets({
      page,
      size: 20,
      status_filter: statusFilter === 'all' ? undefined : statusFilter,
    }),
    placeholderData: keepPreviousData,
  })

  const tickets = ticketsResponse?.tickets || []
  const total = ticketsResponse?.total || 0
  const totalPages = ticketsResponse?.pages || 1

  return (
    <div className='space-y-6'>
      <div className='flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4'>
        <div>
          <h1 className='text-2xl font-bold'>Ticket History</h1>
          <p className='text-muted-foreground'>View and manage your communication tickets</p>
        </div>
        <Link
          to='/tickets/create'
          className='inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors'
        >
          <TicketPlus className='h-4 w-4' />
          Create Ticket
        </Link>
      </div>

      <div className='rounded-xl border border-border bg-card p-4'>
        <div className='flex flex-col sm:flex-row gap-4'>
          <div className='relative flex-1'>
            <Search className='absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground' />
            <input
              type='text'
              placeholder='Search tickets...'
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
              className='w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary'
            />
          </div>
          <div className='relative'>
            <Filter className='absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground' />
            <select
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value as any); setPage(1) }}
              className='pl-10 pr-8 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary appearance-none'
            >
              <option value='all'>All Status</option>
              <option value='pending'>Pending</option>
              <option value='approved'>Approved</option>
              <option value='rejected'>Rejected</option>
              <option value='assigned'>Assigned</option>
              <option value='active'>Active</option>
              <option value='completed'>Completed</option>
              <option value='cancelled'>Cancelled</option>
            </select>
          </div>
        </div>
      </div>

      <div className='rounded-xl border border-border bg-card overflow-hidden'>
        {isLoading ? (
          <div className='p-8 text-center'>
            <Loader2 className='h-8 w-8 animate-spin mx-auto text-primary mb-4' />
            <p className='text-muted-foreground'>Loading tickets...</p>
          </div>
        ) : tickets.length === 0 ? (
          <div className='p-12 text-center'>
            <TicketPlus className='h-16 w-16 mx-auto text-muted-foreground/50 mb-4' />
            <h3 className='text-lg font-medium mb-2'>No tickets found</h3>
            <p className='text-muted-foreground mb-6'>Get started by creating your first communication ticket</p>
            <Link to='/tickets/create' className='inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90'>
              <TicketPlus className='h-4 w-4' />
              Create Ticket
            </Link>
          </div>
        ) : (
          <>
            <div className='overflow-x-auto'>
              <table className='w-full'>
                <thead className='bg-muted/50'>
                  <tr className='border-b border-border'>
                    <th className='px-4 py-3 text-left text-sm font-medium text-muted-foreground'>Title</th>
                    <th className='px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell'>Domain</th>
                    <th className='px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden lg:table-cell'>Languages</th>
                    <th className='px-4 py-3 text-left text-sm font-medium text-muted-foreground'>Status</th>
                    <th className='px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell'>Created</th>
                    <th className='px-4 py-3 text-right text-sm font-medium text-muted-foreground'>Actions</th>
                  </tr>
                </thead>
                <tbody className='divide-y divide-border'>
                  {tickets.map(ticket => (
                    <tr key={ticket.id} className='hover:bg-accent/50 transition-colors'>
                      <td className='px-4 py-4'>
                        <Link to='/tickets/history' className='font-medium hover:text-primary transition-colors'>
                          {ticket.title}
                        </Link>
                        <p className='text-sm text-muted-foreground truncate max-w-xs mt-1'>{ticket.description}</p>
                      </td>
                      <td className='px-4 py-4 hidden md:table-cell'>
                        <span className='px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary'>
                          {ticket.domain}
                        </span>
                      </td>
                      <td className='px-4 py-4 hidden lg:table-cell'>
                        <span className='text-sm text-muted-foreground'>
                          {ticket.source_language} → {ticket.target_language}
                        </span>
                      </td>
                      <td className='px-4 py-4'>
                        <span className={cn(
                          'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
                          statusColors[ticket.status as TicketStatus]
                        )}>
                          <StatusIcon status={ticket.status} />
                          {ticket.status}
                        </span>
                      </td>
                      <td className='px-4 py-4 hidden md:table-cell text-sm text-muted-foreground'>
                        {format(new Date(ticket.created_at), 'MMM d, yyyy')}
                      </td>
                      <td className='px-4 py-4 text-right'>
                        <div className='flex items-center justify-end gap-2'>
                          {ticket.status === 'active' && ticket.room_id && (
                            <Link
                              to={/rooms/}
                              className='inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium bg-primary text-primary-foreground hover:bg-primary/90'
                            >
                              <MessageSquare className='h-3.5 w-3.5' />
                              Join Room
                            </Link>
                          )}
                          <Link
                            to='/tickets/history'
                            className='inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium border border-border hover:bg-accent'
                          >
                            View
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className='px-4 py-3 border-t border-border flex items-center justify-between'>
                <p className='text-sm text-muted-foreground'>
                  Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, total)} of {total} tickets
                </p>
                <div className='flex gap-2'>
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1 || isFetching}
                    className='px-3 py-1.5 rounded-lg border border-border hover:bg-accent disabled:opacity-50'
                  >
                    <ChevronDown className='h-4 w-4 rotate-180' />
                  </button>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages || isFetching}
                    className='px-3 py-1.5 rounded-lg border border-border hover:bg-accent disabled:opacity-50'
                  >
                    <ChevronDown className='h-4 w-4' />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}